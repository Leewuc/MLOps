SCRIPT=`readlink -f $0`
SCRIPT_PATH=`dirname ${SCRIPT}`
PROJECT_PATH=${SCRIPT_PATH}/../../..

cd ${PROJECT_PATH}/src

python main.py \
  --base_date `date -I` \
  --task inference \
  --num_workers 0 \
  --dataset_name prepared_watch_log \
  --model_name ncf