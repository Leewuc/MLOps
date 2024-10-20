#!/bin/bash

############################################################
# Help                                                     
############################################################
Help()
{
   # Display Help
   echo "Add description of the script functions here."
   echo
   echo "Syntax: scriptTemplate [-h|u|s]"
   echo "options:"
   echo "-u     Update target version."
   echo "-s     Service name."
   echo
}

############################################################
# Process the input options. Add options as needed.        
############################################################
u_flag=0
s_flag=0
while getopts :u:s:h flag
do
    case "${flag}" in
        h)
          Help
          exit;;
        u)
          u_flag=1
          update=${OPTARG};;
        s)
          s_flag=1
          service=${OPTARG};;
        :)                                    # If expected argument omitted:
          echo "Error: -${OPTARG} requires an argument."
          exit_abnormal                       # Exit abnormally.
          ;;
    esac
done

if [ $u_flag -eq 0 ]
then
    echo "Error: -u requires an argument."
    Help
    exit 2
elif [ $s_flag -eq 0 ]
then
    echo "Error: -s requires an argument."
    Help
    exit 2
fi


############################################################
# Process service release.                                 
############################################################
VERSION=`python ./version_controller.py next \
	--service_name ${service} \
	--update_type ${update}`
	
if [ -z "$VERSION" ];
then
    echo "VERSION is empty. Exiting."
    exit 1
fi

TAG=${service}-${VERSION}
BRANCH=release-${TAG}
echo "====================================================="
echo "Release Target Info"
echo "  UPDATE : ${update}"
echo " SERVICE : ${service}"
echo " VERSION : ${VERSION}"
echo "     TAG : ${TAG}"
echo "  BRANCH : ${BRANCH}"
echo "====================================================="

git checkout -b ${BRANCH}

echo "Update ${update} version"
python ./version_controller.py ${update} --service_name ${service}

echo "Push new release branch"
git add scripts/build/${service}/VERSION
git commit -m "Release ${TAG}"
git push origin refs/heads/${BRANCH}
git checkout develop
