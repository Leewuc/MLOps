import boto3
import json
from decimal import Decimal
from datetime import datetime


class DynamoDB:
    def __init__(self, aws_region):
        self.resource = boto3.resource("dynamodb", region_name=aws_region)

    def batch_write_df_to_ddb(self, table_name, df):
        table = self.resource.Table(table_name)
        with table.batch_writer() as batch:
            for index, row in df.iterrows():
                batch.put_item(json.loads(row.to_json(), parse_float=Decimal))

    @staticmethod
    def convert_ddb_recommend_schema(
        pk, 
        sk, 
        contents, 
        tz, 
        contents_limit=30, 
        ttl_seconds=3600 * 24 * 3
    ):
        return {
            "PK": pk,
            "SK": sk,
            "RecommendItems": [
                {"ContentID": content["code"], "Score": content["score"]}
                for content in contents[:contents_limit]
            ],
            "CreatedAt": datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S"),
            "TTL": int(datetime.now(tz=tz).timestamp()) + ttl_seconds,
        }
