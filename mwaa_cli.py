import json
import base64
import pprint
import logging

import fire
import boto3
import requests


logging.basicConfig(level=logging.INFO)
client = boto3.client('mwaa')


class MWAACliRequestException(Exception):
    pass


def get_service_variables(mwaa_env_name, service_type, service_name):
    mwaa_cli_command = f"variables get {service_type}/{service_name}/variables"
    stdout = request_with_cli(mwaa_env_name, mwaa_cli_command)
    return json.loads(stdout)


def set_service_variables(mwaa_env_name, service_type, service_name, val):
    request_val = json.dumps(val).replace('"', '\\"')
    mwaa_cli_command = \
        f"variables set {service_type}/{service_name}/variables \"{request_val}\""
    stdout = request_with_cli(mwaa_env_name, mwaa_cli_command)
    return stdout


def request_with_cli(mwaa_env_name, command):
    print(f"run command : {command}")
    mwaa_cli_token = client.create_cli_token(
        Name=mwaa_env_name
    )

    mwaa_auth_token = f"Bearer {mwaa_cli_token['CliToken']}"
    mwaa_webserver_hostname = \
        f"https://{mwaa_cli_token['WebServerHostname']}/aws_mwaa/cli"

    mwaa_response = requests.post(
        mwaa_webserver_hostname,
        headers={
            'Authorization': mwaa_auth_token,
            'Content-Type': 'text/plain'
        },
        data=command
    )

    if mwaa_response.json()["stderr"]:
        stderr = base64.b64decode(mwaa_response.json()["stderr"]).decode('utf8')
        raise MWAACliRequestException(stderr)

    return base64.b64decode(mwaa_response.json()["stdout"]).decode('utf8')


def update_image_version(mwaa_env_name, service_type, service_name, version):
    variables = get_service_variables(
        mwaa_env_name=mwaa_env_name,
        service_type=service_type,
        service_name=service_name
    )

    variables.update({"image": {"version": version}})

    response = set_service_variables(
        mwaa_env_name=mwaa_env_name,
        service_type=service_type,
        service_name=service_name,
        val=variables
    )

    logging.info(pprint.pformat(response))


if __name__ == '__main__':
    fire.Fire({
        "update-version": update_image_version
    })
