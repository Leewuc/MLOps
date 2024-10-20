import sys
import logging
import datetime

from sagemaker.pytorch.processing import PyTorchProcessor
from sagemaker.processing import ProcessingInput, ProcessingOutput

from config.args import parse_args
from config.meta import Tasks
from utils.utils import make_s3_dataset_path
from config.meta import SageMakerMeta
def run_prepare_train_data_task(args, sagemaker_meta):
    output_dst = make_s3_dataset_path(
        base_dir=sagemaker_meta.s3_input_dir,
        dataset_name=f"prepared_{args.dataset_name}",
        dataset_version=args.dataset_version,
        base_date=sagemaker_meta.base_datetime
    ).replace('\\', '/')

    logging.info(f"input_src : {sagemaker_meta.s3_input_src}")
    logging.info(f"output_src : {sagemaker_meta.train_dataset_dir}")
    logging.info(f"output_dst : {output_dst}")
    pytorch_processor = PyTorchProcessor(
        framework_version=args.framework_version,
        py_version=args.py_version,
        code_location=sagemaker_meta.s3_output_dst,
        role=sagemaker_meta.sagemaker_role,
        instance_type=args.instance_type,
        instance_count=1,
        max_runtime_in_seconds=1 * 60 * 60,
    )

    pytorch_processor.run(
        code="main.py",
        source_dir=".",
        arguments=sys.argv[1:] + [
            "--dataset_dir", args.dataset_dir, 
            "--job_name", args.job_name
        ],
        inputs=[
            ProcessingInput(
                source=f"{sagemaker_meta.s3_input_src}/{args.dataset_name}.csv",
                destination=args.dataset_dir
            )
        ],
        outputs=[
            ProcessingOutput(
                source=sagemaker_meta.train_dataset_dir,
                destination=output_dst,
            )
        ],
        job_name=args.job_name,
        wait=True,
    )
def run_prepare_inference_data_task(args, sagemaker_meta):
    logging.info(f"input_src : {sagemaker_meta.s3_input_src}")
    logging.info(f"input_dst : {sagemaker_meta.train_dataset_dir}")
    logging.info(f"output_src : {sagemaker_meta.inference_dataset_dir}")
    logging.info(f"output_dst : {sagemaker_meta.s3_input_src}")

    pytorch_processor = PyTorchProcessor(
        framework_version=args.framework_version,
        py_version=args.py_version,
        code_location=sagemaker_meta.s3_output_dst,
        role=sagemaker_meta.sagemaker_role,
        instance_type=args.instance_type,
        instance_count=1,
        max_runtime_in_seconds=1 * 60 * 60,
    )
    
    pytorch_processor.run(
        code="main.py",
        source_dir=".",
        arguments=sys.argv[1:] + [
            "--dataset_dir", args.dataset_dir, 
            "--job_name", args.job_name
        ],
        inputs=[
            ProcessingInput(
                source=(
                    f"{sagemaker_meta.s3_input_src}/"
                    f"{args.dataset_name}_train_{args.model_name}.snappy.parquet"
                ),
                destination=sagemaker_meta.train_dataset_dir
            )
        ],
        outputs=[
            ProcessingOutput(
                source=sagemaker_meta.inference_dataset_dir,
                destination=sagemaker_meta.s3_input_src,
            )
        ],
        job_name=args.job_name,
        wait=True,
    )
def get_default_local_dir(args):
    if args.task == "train":
        return "/opt/ml"
    else:
        return "/opt/ml/processing"
  if __name__ == '__main__':
    args = parse_args()
    str_datetime = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    if args.job_name == "NoAssigned":
        args.job_name = f"{args.namespace}-{args.model_name}-{args.task}-{str_datetime}"
    default_local_dir = get_default_local_dir(args)
    args.dataset_dir = f"{default_local_dir}/input/data"
    args.output_dir = f"{default_local_dir}/output"
    args.model_dir = f"{default_local_dir}/model"

    sagemaker_meta = SageMakerMeta(args)

    task_map = {
        Tasks.PREPARE_TRAIN_DATA: run_prepare_train_data_task,
        Tasks.PREPARE_INFERENCE_DATA: run_prepare_inference_data_task,
    }

    task = task_map.get(args.task)

    if not task:
        raise KeyError(f"작업을 찾을 수 없습니다 : {args.task}")

    task(args, sagemaker_meta)
