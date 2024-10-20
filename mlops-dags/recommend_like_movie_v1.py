import datetime

import boto3
from botocore.exceptions import ClientError
from pytz import timezone
from airflow import DAG
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup
from airflow.sensors.python import PythonSensor
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator


doc_md = """
### ~님이 좋아할 만한 영화 모델(like-movie)

~와 비슷한 프로그램 추천 띠의 모델 워크플로우입니다.  
각 태스크는 SageMaker SDK를 통해 트리거 역할만 수행하며 
SageMaker의 프로비저닝 된 별도 인스턴스에서 수행됩니다.  
각 태스크는 비동기 센서에 의해 작업 상태를 감지합니다.  
 

#### Notes
- [운영 문서](https://localhost:9999/docs)
"""

user = "<유저명>"  # 수정
tz = "Asia/Seoul"
service_name = "like-movie"
env = Variable.get("env")
variables = Variable.get(f"recommend/{service_name}/variables", deserialize_json=True)
repository_base_uri = variables.get("repo").get("base_uri")
repository_name = variables.get("repo").get("name")
image_version = variables.get("image").get("version")
target_date = variables.get(
    "manual_execution_date",
    "{{ execution_date.in_timezone('Asia/Seoul').strftime('%Y-%m-%d') }}"
)
mwaa_subnets = Variable.get("mwaa", deserialize_json=True).get("subnets")
mwaa_security_groups = Variable.get("mwaa", deserialize_json=True).get("security_groups")

prefix = "mlops"
ecs_cluster = f"{prefix}-airflow-ecs-cluster-{user}"
ecs_task_definition = f"{prefix}-airflow-{service_name}-task-{user}"
ecs_task_container_name = f"airflow-{service_name}-container"
ecs_task_container_image = \
    f"{repository_base_uri}/{repository_name}/{service_name}:{image_version}"
ecs_task_network_configuration = {
    "awsvpcConfiguration": {
        "subnets": mwaa_subnets,
        "securityGroups": mwaa_security_groups,
    },
}


def push_x_com_job(context):
    pass


def register_ecs_task(context):
    print("execute register ecs task")

    ecs = boto3.client("ecs")
    response = ecs.register_task_definition(
        containerDefinitions=[
            {
                "name": context["params"]["container_name"],
                "image": context["params"]["image_uri"],
                "cpu": int(context["params"]["cpu"]),
                "memory": int(context["params"]["memory"]),
                "portMappings": [],
                "essential": True,
                "environment": [],
                "mountPoints": [],
                "volumesFrom": [],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": f"/ecs/{context['params']['task_definition']}",
                        "awslogs-region": "ap-northeast-2",
                        "awslogs-create-group": "true",
                        "awslogs-stream-prefix": "ecs"
                    }
                }
            }
        ],
        taskRoleArn="arn:aws:iam::<ACCOUNT>:role/MLOpsECSTaskExecutionRole",  # 수정
        executionRoleArn="arn:aws:iam::<ACCOUNT>:role/MLOpsECSTaskExecutionRole",  # 수정
        family=context['params']['task_definition'],
        networkMode="awsvpc",
        requiresCompatibilities=["FARGATE"],
        cpu=context["params"]["cpu"],
        memory=context["params"]["memory"]
    )
    print(f"response : {response}")


with DAG(
    dag_id=f"recommend-{service_name}-v1",
    description="~님이 좋아할 만한 영화 모델 워크플로우",
    default_args={
        "owner": "MLOps",
        "depends_on_past": False,
        "retries": 0,
    },
    start_date=datetime.datetime(2024, 3, 6, 0, tzinfo=timezone(tz)),
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    concurrency=3,
    catchup=False,
    dagrun_timeout=datetime.timedelta(hours=5),
    tags=["recommend", "like", "movie", "ecs", "dynamodb", "ncf"],
    doc_md=doc_md,
) as dag:
    task_id = "prepare-train-data"
    namespace = env
    model_name = "ncf"
    job_name = (
        f"{namespace}-{model_name}-{task_id}"
        f"-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    )
    command = [
        "/app/scripts/run/sagemaker/99_run_with_config.sh",
        "-n", namespace,
        "-s", service_name,
        "-t", task_id,
        "-d", target_date,
        "-j", job_name,
    ]
    task = EcsRunTaskOperator(        
        task_id=task_id,
        dag=dag,
        cluster=ecs_cluster,
        task_definition=ecs_task_definition,
        launch_type="FARGATE",
        overrides={
            "containerOverrides": [
                {
                    "name": ecs_task_container_name,
                    "command": command
                },
            ],
        },
        network_configuration=ecs_task_network_configuration,
        execution_timeout=datetime.timedelta(hours=1),
        awslogs_region="ap-northeast-2",
        awslogs_group=f"/ecs/{ecs_task_definition}",
        awslogs_stream_prefix=f"ecs/{ecs_task_container_name}",
        awslogs_fetch_interval=datetime.timedelta(seconds=5),
        params={
            "image_uri": ecs_task_container_image,
            "container_name": ecs_task_container_name,
            "task_definition": ecs_task_definition,
            "cpu": "512",
            "memory": "1024",
        },
        on_execute_callback=register_ecs_task,
    )
