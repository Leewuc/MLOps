import os
import json
import base64
import pprint
import logging
import urllib3
from http.client import responses

import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client('mwaa')


class MWAACliRequestException(Exception):
    pass


def get_mwaa_environment_name(env):
    client = boto3.client("ssm")
    return client.get_parameter(
        Name=f"/<유저명>/{env}/mwaa/env-name",  # 수정
        WithDecryption=True
    )["Parameter"]["Value"]


def request_with_cli(mwaa_env_name, command):
    logger.debug(f"run command : {command}")
    mwaa_cli_token = client.create_cli_token(
        Name=mwaa_env_name
    )

    mwaa_auth_token = f"Bearer {mwaa_cli_token['CliToken']}"
    mwaa_webserver_hostname = \
        f"https://{mwaa_cli_token['WebServerHostname']}/aws_mwaa/cli"

    http = urllib3.PoolManager()
    mwaa_response = http.request(
        method="POST",
        url=mwaa_webserver_hostname,
        headers={
            'Authorization': mwaa_auth_token,
            'Content-Type': 'text/plain'
        },
        body=command
    )
   
    status_code = mwaa_response.status
   
    if status_code != 200:
        err = responses[status_code]
        raise MWAACliRequestException(f"{err} - {mwaa_response.data}")
       
    logger.info(status_code)


def execute_dag(mwaa_env_name, service_type, service_name, version):
    logger.debug(locals())
    dag_id = f"{service_type}-{service_name}-v{version}"
    mwaa_cli_command = f"dags trigger {dag_id}"
    stdout = request_with_cli(mwaa_env_name, mwaa_cli_command)


def parse_namespace(namespace):
    recommend_type, contents_type, _, _, env = namespace.split("/")[-1].split("-")
    return recommend_type, contents_type, env


def lambda_handler(event, _):
    logger.info(event)
    message = json.loads(event["Records"][-1]["Sns"]["Message"])
    recommend_type, contents_type, env = parse_namespace(
        message["Trigger"]["Namespace"]
    )
   
    execute_dag(
        mwaa_env_name=get_mwaa_environment_name(env),
        service_type=os.environ["service_type"],
        service_name=f"{recommend_type}-{contents_type}",
        version=os.environ[f"{recommend_type}_{contents_type}_dag_version"]
    )
