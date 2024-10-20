import os
import re

import fire


version_file_path = os.path.join("scripts", "build", "{SERVICE_NAME}", "VERSION")
version_pattern = "^\d+\.\d+\.\d+"


def get_version(service_name: str):
    """
    해당 서비스 이름의 현재 버전 정보를 가져옵니다.

    Args:
        service_name: 서비스 이름

    Returns:
        버전 정보 x.x.x
    """
    with open(version_file_path.format(SERVICE_NAME=service_name), "r") as f:
        version = f.read().strip()
        if not re.match(version_pattern, version):
            raise ValueError("버전 형식이 잘못 되었습니다")
        return version


def get_next_version(service_name: str, update_type: str):
    version = get_version(service_name)
    major, minor, patch = map(int, version.split('.'))

    if update_type.lower() == "major":
        major += 1
        minor = 0
        patch = 0
    elif update_type.lower() == "minor":
        minor += 1
        patch = 0
    elif update_type.lower() == "patch":
        patch += 1
    else:
        raise ValueError("업데이트 명령이 잘못 되었습니다.")

    return f"{major}.{minor}.{patch}"


def write_version_file(service_name, major: int, minor: int, patch: int):
    with open(version_file_path.format(SERVICE_NAME=service_name), "w") as f:
        f.write(f"{major}.{minor}.{patch}")


def increase_major_version(service_name):
    version = get_version(service_name)
    major, minor, patch = map(int, version.split('.'))
    write_version_file(service_name, major + 1, 0, 0)


def increase_minor_version(service_name):
    version = get_version(service_name)
    major, minor, patch = map(int, version.split('.'))
    write_version_file(service_name, major, minor + 1, 0)


def increase_patch_version(service_name):
    version = get_version(service_name)
    major, minor, patch = map(int, version.split('.'))
    write_version_file(service_name, major, minor, patch + 1)


if __name__ == '__main__':
    fire.Fire({
        'get': get_version,
        'next': get_next_version,
        'major': increase_major_version,
        'minor': increase_minor_version,
        'patch': increase_patch_version,
    })
