import os
import yaml

import fire


project_dir = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(
    project_dir, 
    "scripts", 
    "build", 
    "{SERVICE_NAME}", 
    "config-{NAMESPACE}.yaml"
)


def get_config(namespace, service_name):
    with open(
        config_file_path.format(NAMESPACE=namespace, SERVICE_NAME=service_name), 
        "r"
    ) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def make_script(namespace, task_name, base_date, job, dependency_job, params):
    ns_arg = f"--namespace {namespace}"
    task_arg = f"--task {task_name}"
    base_date_arg = f"--base_date {base_date}"
    job_arg = f"--job_name {job}"
    args = [f"--{key} {val}" for key, val in params.items()]
    if dependency_job:
        args.extend(["--dependency_job_name", dependency_job])
    return ' '.join([ns_arg, task_arg, base_date_arg, job_arg, *args])


def get_run_script(
    namespace, 
    service_name, 
    task_name, 
    base_date, 
    job, 
    dependency_job=None
):
    config = get_config(namespace=namespace, service_name=service_name)
    params = config["parameters"]["tasks"][task_name.lower().replace("-", "_")]
    return make_script(
        namespace=namespace,
        task_name=task_name,
        base_date=base_date,
        job=job,
        dependency_job=dependency_job,
        params=params
    )


if __name__ == '__main__':
    fire.Fire({
        "get-run-script": get_run_script
    })
