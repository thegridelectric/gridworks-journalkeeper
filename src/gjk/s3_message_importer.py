import itertools
import logging
import sys
from datetime import datetime, timedelta

import boto3
import dotenv

from gjk.config import Settings


class S3MessageImporter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.s3 = boto3.client("s3")
        self.aws_bucket_name = "gwdev"
        self.world_instance_name = "hw1__1"
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def get_messages(self, start: datetime, duration: timedelta | None):
        dt = start
        prefix = f'{self.world_instance_name}/eventstore/{dt.strftime("%Y%m%d")}'
        paginator = self.s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.aws_bucket_name, Prefix=prefix)

        date_results = []
        for page in itertools.islice(pages, 1):
            for s3_object in page["Contents"]:
                s3_key = s3_object["Key"]
                try:
                    [from_alias, type_name, message_persisted_ms_str, source] = (
                        s3_key.split("/")[-1].split("-")
                    )
                    persist_time = datetime.fromtimestamp(
                        int(message_persisted_ms_str) / 1000
                    )
                    if persist_time <= start:
                        date_results.append({
                            "s3_key": s3_key,
                            "persist_time": persist_time,
                        })

                except Exception as e:
                    logging.warning(f"Failed file name parsing with {s3_key}")
                    logging.exception(e)

        date_results.sort(key=lambda x: x["persist_time"], reverse=True)
        for result in date_results:
            s3_object = self.s3.get_object(
                Bucket=self.aws_bucket_name, Key=result["s3_key"]
            )
            msg_bytes = s3_object["Body"].read()
            msg_text = msg_bytes.decode("utf-8")
            yield msg_text

        # s3_objects = self.s3.list_objects_v2(
        #     Bucket=self.aws_bucket_name,
        #     Prefix=prefix
        # )
        print("done")

        # date_list = self.get_date_folder_list(start_s, duration_hrs)

        # blist = self.get_single_asset_filenames(start_s, duration_hrs, short_alias)


def __main__():
    settings = Settings(_env_file=dotenv.find_dotenv())
    result = S3MessageImporter(settings).get_messages(
        datetime(2026, 4, 8, 15, 0, 0), timedelta(minutes=60)
    )
    first10 = list(itertools.islice(result, 10))


__main__()
