import os
import pprint
import logging
from datetime import datetime

import pandas as pd
from pytz import timezone

from utils.utils import init_dirs
from common.ddb import DynamoDB


class WatchLogNCFPostProcess:
    def __init__(self, args):
        self.args = args
        self.base_date = datetime.strptime(args.base_date, "%Y-%m-%d")

        self.dataset_src = os.path.join(self.args.output_dir, "inference")
        self.dst = os.path.join(self.args.output_dir, "postprocess")
        init_dirs(self.dataset_src, self.dst)

    def load_dataset(self):
        return pd.read_parquet(
            os.path.join(self.dataset_src, "inference_result.snappy.parquet")
        )

    def run(self):
        df = self.load_dataset()
        ddb = DynamoDB(self.args.aws_region)
        recommend_data = [
            ddb.convert_ddb_recommend_schema(
                pk="C#popular" if idx == 0 else f"U#{str(row['user_id'])}",
                sk=(
                    f"V#{self.args.serve_data_version}#"
                    f"RT#{self.args.serve_recommend_type}#"
                    f"CT#{self.args.serve_contents_type}"
                ),
                contents=row["items"],
                tz=timezone(self.args.timezone),
                contents_limit=self.args.serve_contents_limit,
                ttl_seconds=self.args.serve_data_ttl,
            )
            for idx, row in df.iterrows()
        ]
        logging.info(pprint.pformat(recommend_data[:10]))

        recommend_df = pd.DataFrame.from_records(recommend_data)
        ddb.batch_write_df_to_ddb(
            table_name=self.args.serve_ddb_table_name, df=recommend_df
        )


class WatchLogNCFPreprocessor(WatchLogNCFPostProcess):
    def __init__(self, args):
        super().__init__(args)
