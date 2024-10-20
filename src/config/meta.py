from datetime import datetime

from sagemaker.session import Session
from sagemaker.local.local_session import LocalSession

from utils.utils import make_s3_dataset_path, make_s3_model_output_path
class SageMakerMeta:
    def __init__(self, args):
        self.is_local_mode = "local" in args.instance_type.lower()
        self.sagemaker_role = \
            "arn:aws:iam::<ACCOUNT>:role/MLOpsSageMakerExecutionRole"  # <ACCOUNT> 수정
        self.sagemaker_session = LocalSession() if self.is_local_mode else Session()
        self.base_datetime = datetime.strptime(args.base_date, "%Y-%m-%d")
        self.str_datetime = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        self.train_dataset_dir = f"{args.dataset_dir}/train"
        self.inference_dataset_dir = f"{args.dataset_dir}/inference"
        self.inference_output_dir = f"{args.output_dir}/inference"
        self.s3_base_path = \
            f"s3://mlops-recommend-system-<유저명>/ns={args.namespace}"  # <유저명> 수정
        self.s3_input_dir = f"{self.s3_base_path}/input/data"
        self.s3_input_src = make_s3_dataset_path(
            base_dir=self.s3_input_dir,
            dataset_name=args.dataset_name,
            dataset_version=args.dataset_version,
            base_date=self.base_datetime
        ).replace('\\', '/')
        self.s3_output_dir = f"{self.s3_base_path}/output"
        self.s3_output_dst = make_s3_model_output_path(
            base_dir=self.s3_output_dir,
            model_name=args.model_name,
            base_date=self.base_datetime
        ).replace('\\', '/')
