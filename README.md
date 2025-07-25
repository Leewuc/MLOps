# MLOps 예제 레포지토리

이 프로젝트는 추천 모델 학습과 배포 과정을 자동화하기 위한 MLOps 샘플입니다.
레포 내 스크립트와 파이프라인을 통해 Docker 이미지 빌드부터
SageMaker 학습, Airflow 오케스트레이션, 배포 자동화까지 전 과정을 실습할 수 있습니다.

## 주요 구성

- **src/** : 데이터 전처리, 모델 학습/추론 코드와 공용 유틸리티가 위치합니다.
- **scripts/build/** : Dockerfile과 환경별 설정 파일이 있으며, `build.sh` 로 이미지를 빌드해 ECR에 업로드합니다.
- **scripts/run/** : 로컬 또는 SageMaker 환경에서 각 작업을 실행하기 위한 셸 스크립트가 있습니다.
- **mlops-dags/** : Airflow에서 실행할 DAG 정의를 포함합니다. 예시 DAG는 ECS에서 학습 태스크를 실행하도록 구성되어 있습니다.
- **mlops-monitoring/** : CloudWatch 지표 생성을 위한 예제 스크립트가 있습니다.
- **lambda_function.py** : SNS 이벤트를 받아 MWAA(Airflow) DAG 실행을 트리거하는 Lambda 함수 예제입니다.
- **lambda_update.py** : Lambda 코드를 압축 후 버전을 발행하고, 프로비저닝 동시성 및 오토스케일링을 관리하는 도구입니다.
- **api-test/** : wrk를 이용한 간단한 API 부하 테스트 스크립트가 포함됩니다.
- **buildspec-dev.yaml** : AWS CodeBuild에서 사용되는 빌드 스펙 예시입니다.

## 실행 흐름 예시

1. `build.sh -s <service>` 명령으로 서비스용 Docker 이미지를 빌드해 ECR에 푸시합니다.
2. `release.sh -u <update> -s <service>` 를 이용해 버전을 관리하고 릴리즈 브랜치를 생성합니다.
3. Airflow(MWAA)에서는 `mlops-dags/` 내 DAG을 통해 ECS/SageMaker 작업을 순차 실행합니다.
4. 학습 완료 후 `lambda_update.py` 를 사용해 Lambda 함수를 업데이트하고 별칭 및 프로비저닝 설정을 관리합니다.
5. `mlops-monitoring/metric_generator.py` 를 실행하면 CloudWatch 지표 생성 및 복사 과정을 테스트할 수 있습니다.

각 스크립트의 AWS 계정 정보(`ACCOUNT`, `유저명` 등)는 사용 환경에 맞게 수정해야 합니다.

## 로컬 테스트

`scripts/run/local/00_run_all.sh` 를 실행하면 데이터 준비부터 학습, 추론까지의 전체 과정을 로컬 환경에서 순차적으로 실행합니다. 샘플 데이터는 `local/input/data/watch_log.csv` 에 포함되어 있습니다.

---
본 레포지토리는 MLOps 파이프라인 구축 흐름을 학습하기 위한 예제로, 실제 운영 시에는 보안 설정과 인프라 자원 구성이 추가로 필요합니다.
