FROM python:3.8-buster

RUN apt-get update && \
    pip install -U pip

ARG DOCKERFILE_PATH=${DOCKERFILE_PATH}
ARG AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}
ENV AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}
COPY ${DOCKERFILE_PATH}/requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

COPY . /app
RUN find /app/scripts -name "*.sh" -exec chmod +x {} \;
WORKDIR /app
