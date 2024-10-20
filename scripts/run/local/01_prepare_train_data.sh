SCRIPT=`readlink -f $0`
SCRIPT_PATH=`dirname ${SCRIPT}`
PROJECT_PATH=${SCRIPT_PATH}/../../..

cd ${PROJECT_PATH}/src

python main.py \
  --base_date `date -I` \
  --task prepare-train-data \
  --log_level 10 \
  --model_name ncf