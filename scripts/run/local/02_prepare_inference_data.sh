SCRIPT=`readlink -f $0`
SCRIPT_PATH=`dirname ${SCRIPT}`
PROJECT_PATH=${SCRIPT_PATH}/../../..

cd ${PROJECT_PATH}/src

python main.py \
  --base_date `date -I` \
  --task prepare-inference-data \
  --dataset_name prepared_watch_log \
  --model_name ncf