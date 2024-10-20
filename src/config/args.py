def parse_common_arguments(parser):
    # 기존 코드 아래에 추가
    parser.add_argument("--namespace", type=str, default=None)
    parser.add_argument("--aws_region", type=str, default="ap-northeast-2")
    parser.add_argument("--instance_type", type=str, default="local")
    parser.add_argument("--use_spot", type=bool, default=False)
    parser.add_argument("--py_version", type=str, default="py38")
    parser.add_argument("--framework_version", type=str, default="1.12")
    parser.add_argument("--job_name", type=str, default="NoAssigned")
    parser.add_argument("--dependency_job_name", type=str, default="NoAssigned")
