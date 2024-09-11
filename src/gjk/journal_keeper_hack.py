import math
import uuid
from contextlib import contextmanager
from typing import List, Optional

import boto3
import pendulum
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk import codec
from gjk.config import Settings
from gjk.first_season import beech_channels
from gjk.first_season.beech_batches import beech_br_from_status
from gjk.models import bulk_insert_messages
from gjk.type_helpers import Message
from gjk.types import (
    BatchedReadings,
    GridworksEventGtShStatus,
    HeartbeatA,
    KeyparamChangeLog,
    PowerWatts,
)
from gjk.utils import FileNameMeta, str_from_ms

start_time = pendulum.datetime(2024, 2, 12, 0, 0, 0, tz="America/New_York")
start_s = int(start_time.timestamp())


class JournalKeeperHack:
    def __init__(self, settings: Settings):
        self.settings = settings
        engine = create_engine(settings.db_url.get_secret_value())
        self.Session = sessionmaker(bind=engine)
        self.s3 = boto3.client("s3")
        self.aws_bucket_name = "gwdev"
        self.world_instance_name = "hw1__1"
        self.check_data_channel_consistency()

    @contextmanager
    def get_session(self):
        """Context manager to provide a new session for each task."""
        session = self.Session()
        try:
            yield session
            session.commit()  # Commit if everything went well
        except Exception:
            session.rollback()  # Rollback in case of an error
            raise  # Re-raise the exception after rollback
        finally:
            session.close()  # Always close the session

    def check_data_channel_consistency(self):
        """
        Can take this out when hardware layout for house 0 is fully
        implemented
        """
        with self.get_session() as session:
            beech_channels.data_channels_match_db(session)

    def get_date_folder_list(self, start_s: int, duration_hrs: int) -> List[str]:
        folder_list: List[str] = []

        if self.has_this_days_folder(int(start_s)):
            folder_list.append(pendulum.from_timestamp(start_s).strftime("%Y%m%d"))
        if duration_hrs < 1:
            return folder_list
        add_hrs = 1
        while add_hrs < duration_hrs:
            t = start_s + add_hrs * 3600
            if pendulum.from_timestamp(t).strftime("%Y%m%d") not in folder_list:
                if self.has_this_days_folder(t):
                    folder_list.append(pendulum.from_timestamp(t).strftime("%Y%m%d"))
            add_hrs += 1
        return list(set(folder_list))

    def has_this_days_folder(self, time_s: int) -> bool:
        d = pendulum.from_timestamp(time_s)
        this_days_folder_name = d.strftime("%Y%m%d")
        prefix = f"{self.world_instance_name}/eventstore/{this_days_folder_name}"

        r = self.s3.list_objects_v2(Bucket=self.aws_bucket_name, Prefix=prefix)
        if "Contents" in r.keys():
            return True
        return False

    def get_all_filenames(
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

    def get_single_asset_filenames(
        self,
        start_s: int,
        duration_hrs: int,
        short_alias: str,
    ) -> List[FileNameMeta]:
        date_list = self.get_date_folder_list(start_s, duration_hrs)
        print(f"Loading filenames from folders {date_list}")
        all_fns: List[FileNameMeta] = self.get_all_filenames(date_list)
        start_ms = start_s * 1000
        end_ms = (start_s + duration_hrs * 3600) * 1000 + 400
        ta_list: List[FileNameMeta] = [
            fn
            for fn in all_fns
            if (
                ("status" in fn.type_name)
                or ("power.watts" in fn.type_name)
                or ("keyparam.change.log" in fn.type_name)
            )
            and (short_alias in fn.from_alias)
            and (start_ms <= fn.message_persisted_ms < end_ms)
        ]

        ta_list.sort(key=lambda x: x.message_persisted_ms)
        print(f"total filenames to: {len(ta_list)}")
        print(
            f"First file persisted {str_from_ms(ta_list[0].message_persisted_ms)} America/NY"
        )
        print(
            f"Last file persisted at {str_from_ms(ta_list[-1].message_persisted_ms)} America/NY"
        )
        return ta_list

    def load_messages_from_s3(
        self, start_s: int, duration_hrs: int, short_alias: str
    ) -> List[Message]:
        """
        Load messages from S3,in batches of 100
        """
        blist = self.get_single_asset_filenames(start_s, duration_hrs, short_alias)
        for i in range(math.ceil(len(blist) / 100)):
            first = blist[i * 100]
            print(
                f"loading messages {i * 100} - {i * 100 + 100} [{str_from_ms(first.message_persisted_ms)} America/NY]"
            )

            messages: List[Message] = []
            blank_statuses = 0
            for fn in blist[i * 100 : i * 100 + 100]:
                # get the serialized byte string
                msg_bytes = self.get_message_bytes(fn)
                if fn.type_name == "keyparam.change.log":
                    # Something hinky in the coding of these messages, which
                    # I sent via mosquitto_pub.
                    # It had an extra b:
                    # b'b{"AboutNodeAlias": "beech"}'
                    print(f"Got {fn.file_name}!")
                    json_str = msg_bytes.decode("utf-8")[1:]
                    msg_bytes = json_str.encode("utf-8")

                try:
                    t = codec.from_type(msg_bytes)
                except Exception as e:
                    raise Exception(f"Problem with {fn.file_name}") from e

                if t is None:
                    raise Exception(f"Unrecognized message! {t}")
                # Transform status messages into BatchedReadings
                if isinstance(t, GridworksEventGtShStatus):
                    t = beech_br_from_status(t, fn)

                # msg may be None if not something we are tracking (comms stuff), or
                # if it is a status message with no data readings
                try:
                    msg = tuple_to_msg(t, fn)
                except Exception as e:
                    print(f"Problem with {fn.file_name}: {e}")
                if msg:
                    messages.append(msg)
                elif t.type_name == "batched.readings":
                    blank_statuses += 1

        print(f"For messages {i * 100} - {i * 100 + 100}: {blank_statuses} blanks")
        msg_sql_list = [codec.pyd_to_sql(x) for x in messages]
        with self.get_session() as session:
            bulk_insert_messages(session, msg_sql_list)
            session.commit()

    def get_message_bytes(self, file_name_meta: FileNameMeta) -> bytes:
        s3_object = self.s3.get_object(
            Bucket=self.aws_bucket_name, Key=file_name_meta.file_name
        )
        msg_as_bytes = s3_object["Body"].read()
        return msg_as_bytes


def tuple_to_msg(t: HeartbeatA, fn: FileNameMeta) -> Optional[Message]:
    """
    Take a tuple along with the meta data from the filename
    in the persistent store and return the Message to be put in the messages table
    of the journaldb.

    If the tuple is a BatchedReadings message with no actual readings, returns None
    If the tuple is not in the list of messages we are tracking in journaldb, also
    returns None
    """

    if isinstance(t, BatchedReadings):
        return batchedreading_to_msg(t, fn)
    elif isinstance(t, PowerWatts):
        return basic_to_msg(t, fn)
    elif isinstance(t, KeyparamChangeLog):
        return basic_to_msg(t, fn)
    elif isinstance(t, GridworksEventGtShStatus):
        return gridworkseventgtshstatus_to_msg(t, fn)
    else:
        return None


def batchedreading_to_msg(t: BatchedReadings, fn: FileNameMeta) -> Optional[Message]:
    if t.data_channel_list == []:
        return None
    else:
        return Message(
            message_id=t.id,
            from_alias=t.from_g_node_alias,
            message_persisted_ms=fn.message_persisted_ms,
            payload=t.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.message_created_ms,
        )


def gridworkseventgtshstatus_to_msg(
    t: GridworksEventGtShStatus, fn: FileNameMeta
) -> Optional[Message]:
    return Message(
        message_id=t.status.status_uid,
        from_alias=t.status.from_g_node_alias,
        message_persisted_ms=fn.message_persisted_ms,
        payload=t.to_dict(),
        message_type_name=t.type_name,
        message_created_ms=int(t.time_n_s / 10**6),
    )


def basic_to_msg(t: HeartbeatA, fn: FileNameMeta) -> Message:
    return Message(
        message_id=str(uuid.uuid4()),
        from_alias=fn.from_alias,
        message_type_name=t.type_name,
        message_persisted_ms=fn.message_persisted_ms,
        payload=t.to_dict(),
        message_created_ms=None,
    )
