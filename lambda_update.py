import os
import glob
import yaml
import pprint
import logging
from zipfile import ZipFile
from time import sleep

import boto3

logging.basicConfig(level=logging.INFO)


class LambdaAutoScalingMeta:
    """Lambda 오토스케일링 관련 메타데이터"""
    def __init__(self, function_name):
        self.service_name = "lambda"
        self.scalable_dimension = "lambda:function:ProvisionedConcurrency"
        self.resource_id = f"function:{function_name}" + ":{ALIAS}"


class LambdaUpdateException(Exception):
    pass


class LambdaUpdate(LambdaAutoScalingMeta):
    """
    람다 업데이트 자동화를 위한 기능
    """
    EXCLUDE_PACKAGE_PATTERNS = [
        "venv",
        "venv/**",
        "scripts",
        "scripts/**",
        "update_lambda.py",
        "*.zip"
    ]

    def __init__(self, env, function_name):
        super().__init__(function_name)
        self.env = env
        self.client = boto3.client("lambda")
        self.autoscaler = boto3.client("application-autoscaling")
        self.function_name = function_name
        self.project_src = os.path.dirname(__file__)
        self.config = None
        self.published_version = None
        self.previous_alias = None
        self.next_alias = None
        self.compressed_code = None
        self.cwd()

    def cwd(self):
        os.chdir(os.path.join(self.project_src, "src"))

    def load_config(self):
        """ 환경별 config 불러오기 """
        config_src = os.path.join(self.project_src, "config", f"{self.env}.yaml")
        with open(config_src, "r") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

    def get_target_files(self):
        """
        업데이트 코드 리스트 가져오기.
        EXCLUDE_PACKAGE_PATTERNS 패턴에 해당하는 파일은 제외됩니다.
        """
        targets = set(glob.glob("**", recursive=True))
        for pattern in self.EXCLUDE_PACKAGE_PATTERNS:
            targets -= set(glob.glob(pattern, recursive=True))
        return list(targets)

    def compress_code(self):
        """ 배포 대상 코드를 압축합니다 """
        logging.info("Compress Code...")
        targets = self.get_target_files()
        zip_file_name = f"{self.function_name}.zip"
        with ZipFile(zip_file_name, "w") as zf:
            for target in targets:
                zf.write(target)

    def get_compressed_code(self):
        return open(f"{self.function_name}.zip", "rb").read()

    def wait_for_function_updated(self, wait_interval_seconds=5, max_wait_seconds=60):
        """ 람다의 최근 업데이트가 완료 될 때까지 기다립니다. """
        wait_count = max_wait_seconds // wait_interval_seconds
        response = None
        for _ in range(wait_count):
            response = self.client.get_function(FunctionName=self.function_name)

            if response["Configuration"]["LastUpdateStatus"].lower() != "successful":
                sleep(wait_interval_seconds)
                continue

            return True, response
        return False, response

    def update_function_configuration(self):
        """ Config 업데이트를 수행합니다. """
        logging.info("Update Function Configuration...")
        self.load_config()
        response = self.client.update_function_configuration(
            FunctionName=self.function_name,
            **self.config
        )
        logging.info(pprint.pformat(response))
        return self

    def update_function_code(self):
        """ 코드 업데이트를 수행합니다. """
        logging.info("Update Function Code...")
        self.compress_code()
        response = self.client.update_function_code(
            FunctionName=self.function_name,
            ZipFile=self.get_compressed_code()
        )
        logging.info(pprint.pformat(response))
        return self

    def publish_version(self, description):
        """
        신규 버전을 발행하고 버전명을 저장합니다.
        버전명은 자동 순차 증가입니다.
        """
        logging.info("Publish Version...")
        response = self.client.publish_version(
            FunctionName=self.function_name,
            Description=description
        )
        logging.info(pprint.pformat(response))
        self.published_version = response["Version"]
        return self

    def get_latest_alias_version(self):
        """
        가장 최근 별칭명을 가져옵니다.
            - 별칭명은 v{n} 형태의 별칭만 유효합니다.
            - v{n} 별칭 중 가장 높은 n의 별칭을 반환합니다.

        :return: 최근 별칭명
        """
        logging.info("Get Latest Alias...")
        aliases = []
        paginator = self.client.get_paginator("list_aliases")
        page_iterator = paginator.paginate(
            FunctionName=self.function_name,
            MaxItems=100
        )
        for page in page_iterator:
            aliases.extend([alias["Name"] for alias in page["Aliases"]])

        if not aliases:
            return 0

        max_version = self._parse_max_version(aliases)

        return max_version

    @staticmethod
    def _parse_max_version(aliases):
        """ 별칭명 파서 """
        return max([int(alias[1:]) for alias in aliases if alias.startswith("v")])

    def create_alias(self):
        """
        신규 별칭을 생성합니다.

        발행 이력이 없는 경우 : v1
        발행 이력이 있는 경우 : v{n+1}
        """
        logging.info("Create Alias...")
        latest_alias = self.get_latest_alias_version()
        self.previous_alias = f"v{latest_alias}"
        self.next_alias = f"v{latest_alias + 1}"
        if not self.published_version:
            raise LambdaUpdateException("발행 된 버전이 없습니다!")

        response = self.client.create_alias(
            FunctionName=self.function_name,
            Name=self.next_alias,
            FunctionVersion=self.published_version
        )
        logging.info(pprint.pformat(response))
        return self

    def add_invoke_permission_to_gateway(self, gateway_arn):
        """
        API Gateway에 Lambda 호출 권한을 부여합니다.
        호출 가능 범위는 */GET/*/* 입니다.
        (모든 스테이지, GET 메서드, 2depth 까지의 모든 리소스)

        :param gateway_arn: 권한을 부여할 API Gateway의 ARN
        """
        logging.info("Add Invoke Permission to API Gateway")
        if not self.next_alias:
            raise LambdaUpdateException("배포 된 별칭이 없습니다!")
        response = self.client.add_permission(
            FunctionName=f"{self.function_name}:{self.next_alias}",
            StatementId=f"{self.env}-{self.next_alias}",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"{gateway_arn}/*/GET/*/*",
        )
        logging.info(pprint.pformat(response))
        return self

    def get_provisioned_concurrency(self, alias):
        """
        대상 별칭의 프로비저닝 동시성을 가져옵니다.
        (이전 별칭의 프로비저닝 동시성을 가져와 동일하게 설정해주기 위함)

        이전 별칭이 없거나 프로비저닝 동시성이 없다면 1으로 설정됩니다.
        """
        logging.info("Get Previous Provisioned Concurrency")

        try:
            response = self.client.get_provisioned_concurrency_config(
                FunctionName=self.function_name,
                Qualifier=alias,
            )
        except Exception as e:
            logging.info(e)
            logging.info("배포된 이전 버전이 없습니다.\n기본 동시성 1을 반환합니다.")
            return 1

        logging.info(pprint.pformat(response))
        return response["AllocatedProvisionedConcurrentExecutions"]

    def set_provisioned_concurrency(self, alias, need=1):
        """ 대상 별칭의 프로비저닝 동시성 설정 """
        logging.info("Set Provisioned Concurrency")
        response = self.client.put_provisioned_concurrency_config(
            FunctionName=self.function_name,
            Qualifier=alias,
            ProvisionedConcurrentExecutions=need,
        )
        logging.info(pprint.pformat(response))
        return self

    def delete_provisioned_concurrency(self, alias):
        """
        대상 별칭의 프로비저닝 동시성 삭제
        (정상 배포 이후 이전 별칭의 프로비저닝 동시성 삭제를 위함)
        """
        logging.info("Delete Provisioned Concurrency")
        response = self.client.delete_provisioned_concurrency_config(
            FunctionName=self.function_name,
            Qualifier=alias,
        )
        logging.info(pprint.pformat(response))
        return self

    def add_provisioned_concurrency_autoscaling(
        self, 
        alias, 
        min_capacity=1, 
        max_capacity=10, 
        target_value=0.3
    ):
        """
        프로비저닝 동시성 오토스케일링을 추가합니다.
        - 오토스케일링 대상 등록
        - 오토스케일링 정책 등록
        """
        response = self.autoscaler.register_scalable_target(
            ServiceNamespace=self.service_name,
            ResourceId=self.resource_id.format(ALIAS=alias),
            ScalableDimension=self.scalable_dimension,
            MinCapacity=min_capacity,
            MaxCapacity=max_capacity,
        )
        logging.info(pprint.pformat(response))

        response = self.autoscaler.put_scaling_policy(
            PolicyName="lambda-common-autoscaling-policy",
            ServiceNamespace=self.service_name,
            ResourceId=self.resource_id.format(ALIAS=alias),
            ScalableDimension=self.scalable_dimension,
            PolicyType="TargetTrackingScaling",
            TargetTrackingScalingPolicyConfiguration={
                "TargetValue": target_value,
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": "LambdaProvisionedConcurrencyUtilization"
                }
            },
        )
        logging.info(pprint.pformat(response))
        return self

    def delete_provisioned_concurrency_autoscaling(self, alias):
        """
        대상 별칭의 프로비저닝 동시성 오토스케일링을 삭제합니다.
        (정상 배포 이후 이전 별칭의 프로비저닝 동시성 오토스케일링 삭제를 위함)
        """
        response = self.autoscaler.deregister_scalable_target(
            ServiceNamespace=self.service_name,
            ResourceId=self.resource_id.format(ALIAS=alias),
            ScalableDimension=self.scalable_dimension,
        )
        logging.info(pprint.pformat(response))
        return self

    def describe_provisioned_concurrency_autoscaling(self):
        response = self.get_scalable_targets()
        logging.info(pprint.pformat(response))

        response = self.get_scaling_policies()
        logging.info(pprint.pformat(response))
        return self

    def get_scalable_targets(self):
        if not self.next_alias:
            raise LambdaUpdateException("배포 된 별칭이 없습니다!")
        response = self.autoscaler.describe_scalable_targets(
            ServiceNamespace=self.service_name,
            ResourceIds=self.resource_id.format(ALIAS=self.next_alias),
            ScalableDimension=self.scalable_dimension,
        )
        return response["ScalableTargets"]

    def get_scaling_policies(self):
        if not self.next_alias:
            raise LambdaUpdateException("배포 된 별칭이 없습니다!")
        response = self.autoscaler.describe_scaling_policies(
            PolicyNames=["lambda-common-autoscaling-policy"],
            ServiceNamespace=self.service_name,
            ResourceId=self.resource_id.format(ALIAS=self.next_alias),
            ScalableDimension=self.scalable_dimension,
        )
        return response["ScalingPolicies"]

    def run_set_provisioning_autoscaling_process(self):
        """
        프로비저닝 동시성 오토스케일링을 설정합니다.

        1. 이전 별칭의 프로비저닝 동시성 가져오기
        2. 현재 별칭에 이전 별칭과 동일한 동시성 설정
        3. 현재 별칭에 프로비저닝 동시성 오토스케일링 설정
        """
        logging.info("Run Set Provisioning Autoscaling Process")
        if not self.previous_alias:
            raise LambdaUpdateException("이전 별칭 정보가 없습니다!")

        if not self.next_alias:
            raise LambdaUpdateException("배포 된 별칭이 없습니다!")

        previous_concurrency_count = self.get_provisioned_concurrency(
            alias=self.previous_alias
        )
        self.set_provisioned_concurrency(
            alias=self.next_alias, 
            need=previous_concurrency_count
        )
        self.add_provisioned_concurrency_autoscaling(alias=self.next_alias)

    def run_delete_previous_provisioning_autoscaling_process(self):
        """
        프로비저닝 동시성 오토스케일링 삭제를 수행합니다.

        1. 이전 별칭의 프로비저닝 동시성 삭제
        2. 이전 별칭의 프로비저닝 동시성 오토스케일링 삭제
        """
        logging.info("Run Delete Previous Provisioning Autoscaling Process")
        if not self.previous_alias:
            self.previous_alias = f"v{self.get_latest_alias_version() - 1}"

        self.delete_provisioned_concurrency(alias=self.previous_alias)
        self.delete_provisioned_concurrency_autoscaling(alias=self.previous_alias)



