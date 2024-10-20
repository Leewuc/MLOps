#!/bin/bash

############################################################
# Help                                                     
############################################################
Help()
{
   # Display Help
   echo "Add description of the script functions here."
   echo
   echo "Syntax: scriptTemplate [-h|s]"
   echo "options:"
   echo "-s     Service name."
   echo
}

############################################################
# Process the input options. Add options as needed.        
############################################################
s_flag=0
while getopts :s:h flag
do
    case "${flag}" in
        h)
          Help
          exit;;
        s)
          s_flag=1
          service=${OPTARG};;
        :)                                    # If expected argument omitted:
          echo "Error: -${OPTARG} requires an argument."
          exit_abnormal                       # Exit abnormally.
          ;;
    esac
done

if [ $s_flag -eq 0 ]
  then
    echo "Error: -s requires an argument."
    Help
  exit 2
fi

############################################################
# Process docker image build.                              
############################################################
DOCKERFILE_PATH=scripts/build/${service}
BUILD_IMAGE_NAME=${service}
BUILD_VERSION=`python version_controller.py get --service_name ${service}`
REPOSITORY_NAME="mlops/<유저명>/recommend" # 수정
REPOSITORY="<ACCOUNT>.dkr.ecr.ap-northeast-2.amazonaws.com/${REPOSITORY_NAME}" # 수정
AWS_DEFAULT_REGION=ap-northeast-2

echo "====================================================="
echo "Docker Image Build Target Info"
echo "     DOCKERFILE_PATH : ${DOCKERFILE_PATH}"
echo "    BUILD_IMAGE_NAME : ${BUILD_IMAGE_NAME}"
echo "       BUILD_VERSION : ${BUILD_VERSION}"
echo "          REPOSITORY : ${REPOSITORY}"
echo "  AWS_DEFAULT_REGION : ${AWS_DEFAULT_REGION}"
echo "====================================================="

echo "LOGIN ECR : ${REPOSITORY}/${BUILD_IMAGE_NAME}"
aws ecr get-login-password \
  --region ${AWS_DEFAULT_REGION} | docker login \
  --username AWS \
  --password-stdin ${REPOSITORY}/${BUILD_IMAGE_NAME}

echo "CHECK EXISTS IMAGE IN ECR"
image_info=$(aws ecr describe-images \
						 --repository-name ${REPOSITORY_NAME}/${BUILD_IMAGE_NAME} \
						 --image-ids=imageTag=${BUILD_VERSION} 2> /dev/null)
							
if [[ ! "$image_info" == "" ]]
then
  echo "[!] EXISTS IMAGE : ${REPOSITORY}/${BUILD_IMAGE_NAME}:${BUILD_VERSION}"
  exit 2
else
  echo "[v] Not exists image"
fi

echo "CHECK DOCKERFILE_PATH"
if [ ! -d ${DOCKERFILE_PATH} ]
then
  echo "[!] Not found path or directory : ${DOCKERFILE_PATH}"
  exit 2
else
  echo "[v] Build path : ${DOCKERFILE_PATH}"
fi

echo "BUILD ${BUILD_IMAGE_NAME}:${BUILD_VERSION}"
if [[ "$(docker images -q ${BUILD_IMAGE_NAME}:${BUILD_VERSION} 2> /dev/null)" == "" ]]
then
  docker build \
    -f ${DOCKERFILE_PATH}/Dockerfile \
    --build-arg DOCKERFILE_PATH=${DOCKERFILE_PATH} \
    --build-arg AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} \
    -t ${BUILD_IMAGE_NAME}:${BUILD_VERSION} .
  if [[ "$(docker images -q ${BUILD_IMAGE_NAME}:${BUILD_VERSION} 2> /dev/null)" == "" ]]
  then
    echo "[!] Failed build image : ${BUILD_IMAGE_NAME}:${BUILD_VERSION}"
    exit 2
  fi

  echo "[v] Success build image!"
fi

echo "TAGGING..."
docker tag ${BUILD_IMAGE_NAME}:${BUILD_VERSION} \
  ${REPOSITORY}/${BUILD_IMAGE_NAME}:${BUILD_VERSION}

echo "PUSH : ${REPOSITORY}/${BUILD_IMAGE_NAME}:${BUILD_VERSION}"
docker push ${REPOSITORY}/${BUILD_IMAGE_NAME}:${BUILD_VERSION}

echo "SUCCESS!"
