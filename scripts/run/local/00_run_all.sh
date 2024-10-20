SCRIPT=`readlink -f $0`
SCRIPT_PATH=`dirname ${SCRIPT}`

${SCRIPT_PATH}/01_prepare_train_data.sh
${SCRIPT_PATH}/02_prepare_inference_data.sh
${SCRIPT_PATH}/03_train.sh
${SCRIPT_PATH}/04_inference.sh