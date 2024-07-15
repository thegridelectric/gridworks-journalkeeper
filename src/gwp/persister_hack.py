import json
import typing
from typing import Any
from typing import List
from typing import Optional

import boto3
import pendulum
from pydantic import BaseModel

from gwp.models import Message


start_time = pendulum.datetime(2024, 2, 12, 0, 0, 0, tz="America/New_York")
start_s = int(start_time.timestamp())


class FileNameMeta(BaseModel):
    from_alias: str
    type_name: str
    message_persisted_ms: int
    file_name: str


class PersisterHack:
    def __init__(self):
        self.s3 = boto3.client("s3")
        self.aws_bucket_name = "gwdev"
        self.world_instance_name = "hw1__1"

    def get_date_folder_list(self, start_s: int, duration_hrs: int) -> List[str]:
        folder_list: List[str] = []
        found_latest_earlier: bool = False
        i = 0
        while (not found_latest_earlier) and i < 5:
            t = start_s - 3600 * 24 * (i + 1)
            if self.has_this_days_folder(t):
                folder_list.append(pendulum.from_timestamp(t).strftime("%Y%m%d"))
                found_latest_earlier = True
            i += 1

        if self.has_this_days_folder(int(start_s)):
            folder_list.append(pendulum.from_timestamp(start_s).strftime("%Y%m%d"))

        add_hrs = 0
        while add_hrs < duration_hrs:
            add_hrs += 24
            add_hrs = min(add_hrs, duration_hrs)
            t = start_s + add_hrs * 3600
            if self.has_this_days_folder(t):
                folder_list.append(pendulum.from_timestamp(t).strftime("%Y%m%d"))

        return list(set(folder_list))

    def has_this_days_folder(self, time_s: int) -> bool:
        d = pendulum.from_timestamp(time_s)
        this_days_folder_name = d.strftime("%Y%m%d")
        prefix = f"{self.world_instance_name}/eventstore/{this_days_folder_name}"

        r = self.s3.list_objects_v2(Bucket=self.aws_bucket_name, Prefix=prefix)
        if "Contents" in r.keys():
            return True
        return False

    def get_file_name_meta_list(
        self,
        date_folder_list: List[str],
    ):
        fn_list: List[FileNameMeta] = []
        for date_folder in date_folder_list:
            prefix = f"{self.world_instance_name}/eventstore/{date_folder}/"
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.aws_bucket_name, Prefix=prefix)
            file_name_list = []
            for page in pages:
                for obj in page["Contents"]:
                    file_name_list.append(obj["Key"])

            for file_name in file_name_list:
                try:
                    from_alias = file_name.split("/")[-1].split("-")[0]
                    type_name = file_name.split("/")[-1].split("-")[1]
                    message_persisted_ms = int(file_name.split("/")[-1].split("-")[2])
                except:
                    raise Exception(f"Failed file name parsing with {file_name}")
                fn_list.append(
                    FileNameMeta(
                        from_alias=from_alias,
                        type_name=type_name,
                        message_persisted_ms=message_persisted_ms,
                        file_name=file_name,
                    )
                )

        return fn_list

    def get_messages(
        self, start_time_unix_ms: int, duration_hrs: int, atn_alias: str
    ) -> List[Message]:
        g_node_alias_list = [atn_alias, atn_alias + ".scada"]
        start_time_utc = pendulum.from_timestamp(start_time_unix_ms / 1000)
        end_time_utc = start_time_utc + pendulum.duration(hours=duration_hrs)
        end_time_unix_ms = end_time_utc.int_timestamp * 1000
        date_folder_list = self.get_date_folder_list(start_time_unix_ms, duration_hrs)
        print(f"Got date_folder_list: {date_folder_list}")
        fn_list = self.get_file_name_meta_list(
            start_time_unix_ms=start_time_unix_ms,
            end_time_unix_ms=end_time_unix_ms,
            date_folder_list=date_folder_list,
            g_node_alias_list=g_node_alias_list,
        )

        readings: List[Message] = []
        for i in range(len(fn_list)):
            fn = fn_list[i]
            message_bytes = self.get_message_bytes(fn)

        return readings

    def get_message_bytes(self, file_name_meta: FileNameMeta) -> bytes:
        s3_object = self.s3.get_object(
            Bucket=self.aws_bucket_name, Key=file_name_meta.file_name
        )
        msg_as_bytes = s3_object["Body"].read()
        return msg_as_bytes
