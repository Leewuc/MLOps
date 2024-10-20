import re
from os import environ
from subprocess import check_output

import fire


def validation_branch_name(branch_name: str) -> bool:
    pattern = "^release-.*-\d+\.\d+\.\d+"
    return True if re.match(pattern, branch_name) else False


def get_current_branch(env) -> str:
    if env.lower() == "codebuild":
        return environ["CODEBUILD_WEBHOOK_TRIGGER"].replace("branch/", "").strip()
    else:
        return check_output(
            "git branch --show-current", 
            shell=True
        ).strip().decode("utf-8")


def parse_branch(branch_name: str) -> tuple:
    branch_name = branch_name.replace("release-", "")
    split_branch_name = branch_name.split("-")
    service_name = "-".join(split_branch_name[:-1])
    version = split_branch_name[-1]
    return service_name, version


def get_service_name(env="codebuild"):
    branch_name = get_current_branch(env)
    if not validation_branch_name(branch_name):
        raise ValueError(f"적합하지 않은 브랜치 이름입니다 - {branch_name}")
    return parse_branch(branch_name)[0]


if __name__ == '__main__':
    fire.Fire({
        "get-service-name": get_service_name,
    })

