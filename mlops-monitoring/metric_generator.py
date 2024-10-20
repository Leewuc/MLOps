import time
import datetime
import pprint
import random

import boto3
import pandas as pd


class CustomPutMetricsError(Exception):
    pass


def generate_natural_decrement_data(min_value, max_value, count, reverse=True):
    sign_list = ([-1] * 7) + ([1] * 3)

    value = random.uniform(min_value, max_value)
    result = [value]
    for i in range(count):
        sign = random.choice(sign_list)
        error_rate = random.randint(1, 10 + 1) * 0.005
        value = value + (value * error_rate * sign)
        if value < min_value:
            value = min_value

        if value > max_value:
            value = max_value
        result.append(value)
    return result[::-1] if reverse else result


def generate_time_series(start_datetime=None, total_hours=3, interval_seconds=300):
    if not start_datetime:
        start_datetime = \
            datetime.datetime.utcnow() - datetime.timedelta(hours=total_hours)
    end_datetime = start_datetime + datetime.timedelta(hours=total_hours)

    return pd.date_range(start_datetime, end_datetime, freq=f"{interval_seconds}S")


def generate_metrics(cw, namespace, metric_info):
    """ CloudWatch 매트릭을 생성(Put)합니다. """
    for name, info in metric_info.items():
        times = generate_time_series()
        min_value, max_value = info["ValueRange"]
        values = generate_natural_decrement_data(min_value, max_value, len(times))

        for time, value in zip(times, values):
            print(f"put metric data : {time}, {name}, {round(value, 4)}")
            response = cw.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': name,
                        'Dimensions': info["Dimensions"],
                        'Timestamp': time,
                        'Value': round(value, 4),
                        'Unit': info["Unit"],
                    },
                ]
            )

            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                raise CustomPutMetricsError(pprint.pformat(response))


def copy_metrics(cw, namespace, copy_namespace, metric_info, period=300, lookup_hours=6):
    for name, info in metric_info.items():
        print(info)
        response = cw.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'tempquery',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': namespace,
                            'MetricName': name,
                            'Dimensions': info["Dimensions"]
                        },
                        'Period': period,
                        'Stat': info["Stat"],
                        'Unit': info["Unit"],
                    },
                },
            ],
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=lookup_hours),
            EndTime=datetime.datetime.utcnow(),
        )
        metric_results = response["MetricDataResults"][-1]
        metric_iter = zip(metric_results["Timestamps"], metric_results["Values"])

        for timestamp, value in metric_iter:
            print(f"put metric data : {timestamp}, {name}, {value}")
            response = cw.put_metric_data(
                Namespace=copy_namespace,
                MetricData=[
                    {
                        'MetricName': name,
                        'Dimensions': info["Dimensions"],
                        'Timestamp': timestamp,
                        'Value': value,
                        'Unit': info["Unit"],
                    },
                ]
            )

            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                raise CustomPutMetricsError(pprint.pformat(response))


if __name__ == '__main__':
    user = "<유저명>"
    env = "dev"
    namespace = "/aws/sagemaker/TrainingJobs"
    job_name = f"{env}-ncf-train"
    host_dimensions = [{"Name": "Host", "Value": f"{job_name}/algo-1"}]
    job_dimensions = [{"Name": "TrainingJobName", "Value": job_name}]

    copy_namespace = f"/aws/sagemaker/like-movie-TrainingJobs-{user}-{env}"
    copy_job_name = f"{env}-ncf-train"
    metric_info = {
        "CPUUtilization": {
            "Dimensions": host_dimensions,
            "Stat": "Average",
            "Unit": "Percent",
            "ValueRange": (50, 100 + 1),
        },
        "MemoryUtilization": {
            "Dimensions": host_dimensions,
            "Stat": "Average",
            "Unit": "Percent",
            "ValueRange": (30, 70 + 1),
        },
        "DiskUtilization": {
            "Dimensions": host_dimensions,
            "Stat": "Average",
            "Unit": "Percent",
            "ValueRange": (0, 30 + 1),
        },
        "train:loss": {
            "Dimensions": job_dimensions,
            "Stat": "Average",
            "Unit": "None",
            "ValueRange": (0.8, 1),
        },
        "valid:loss": {
            "Dimensions": job_dimensions,
            "Stat": "Average",
            "Unit": "None",
            "ValueRange": (0.8, 1),
        },
        "NDCG": {
            "Dimensions": job_dimensions,
            "Stat": "Average",
            "Unit": "None",
            "ValueRange": (0.1, 0.2),
        },
    }

    cw = boto3.client("cloudwatch")
    generate_metrics(cw=cw, namespace=namespace, metric_info=metric_info)
    time.sleep(60)
    copy_metrics(
        cw=cw, 
        namespace=namespace, 
        copy_namespace=copy_namespace, 
        metric_info=metric_info
    )
