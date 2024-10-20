import datetime
def make_s3_dataset_path(
    base_dir, 
    dataset_name, 
    dataset_version, 
    base_date: 
    datetime.datetime
):
    return path.join(
        base_dir,
        dataset_name,
        f"v{dataset_version}",
        base_date.strftime("year=%Y"),
        base_date.strftime("month=%m"),
        base_date.strftime("day=%d"),
    )


def make_s3_model_output_path(base_dir, model_name, base_date: datetime.datetime):
    return path.join(
        base_dir,
        model_name,
        base_date.strftime("year=%Y"),
        base_date.strftime("month=%m"),
        base_date.strftime("day=%d"),
    )
