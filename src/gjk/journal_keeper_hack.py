import math
import uuid
from contextlib import contextmanager
from typing import List, Optional

import boto3
import pendulum
from deepdiff import DeepDiff
from gw.errors import DcError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk import codec
from gjk.codec import pyd_to_sql
from gjk.config import Settings
from gjk.first_season import beech_channels, oak_channels
from gjk.first_season.beech_batches import beech_br_from_status
from gjk.first_season.oak_batches import oak_br_from_status
from gjk.models import DataChannelSql, bulk_insert_messages
from gjk.old_types import BatchedReadings, GridworksEventGtShStatus
from gjk.type_helpers import Message
from gjk.types import (
    GridworksEventReport,
    HeartbeatA,
    KeyparamChangeLog,
    PowerWatts,
)
from gjk.utils import FileNameMeta, str_from_ms

start_time = pendulum.datetime(2024, 2, 12, 0, 0, 0, tz="America/New_York")
start_s = int(start_time.timestamp())


class JournalKeeperHack:
    def __init__(self, settings: Settings, alias: str):
        self.settings = settings
        engine = create_engine(settings.db_url.get_secret_value())
        self.Session = sessionmaker(bind=engine)
        self.s3 = boto3.client("s3")
        self.aws_bucket_name = "gwdev"
        self.world_instance_name = "hw1__1"
        self.alias = alias
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

    def check_data_channel_consistency(self, check_missing=True):
        """
        Raises exception if there is a mismatch between data channels
        in code and in database
        """
        with self.get_session() as session:
            consistent = True

            if self.alias == "beech":
                local_channels = beech_channels.BEECH_CHANNELS_BY_NAME.values()
            elif self.alias == "oak":
                local_channels = oak_channels.OAK_CHANNELS_BY_NAME.values()
            else:
                raise ValueError(f"No local channels found for {self.alias}.")
            local_dcs = {pyd_to_sql(dc) for dc in local_channels}

            dcs = {
                dc
                for dc in session.query(DataChannelSql).all()
                if self.alias in dc.terminal_asset_alias
            }

            local_ids = {dc.id for dc in local_dcs}
            ids = {dc.id for dc in dcs}

            # look for missing local channels
            if check_missing:
                if (ids - local_ids) != set():
                    consistent = False
                    print("Missing some channels locally")
                    for id in ids - local_ids:
                        dc = next(dc for dc in dcs if dc.id == id)
                        print(dc.to_dict())

            # look for missing global channels
            if (local_ids - ids) != set():
                consistent = False
                print("Missing some channels in db")
                for id in local_ids - ids:
                    dc = next(dc for dc in local_dcs if dc.id == id)
                    print(dc.to_dict())

            # look for mismatches
            for id in local_ids & ids:
                dc_local = next(dc for dc in local_dcs if dc.id == id)
                dc = next(dc for dc in dcs if dc.id == id)
                dc_local_dict = dc_local.to_dict()
                dc_local_dict.pop("DisplayName")
                dc_dict = dc.to_dict()
                dc_dict.pop("DisplayName")

                # InPowerMetering is optional
                if "InPowerMetering" in dc_dict:
                    dc_dict.pop("InPowerMetering")
                if "InPowerMetering" in dc_local_dict:
                    dc_local_dict.pop("InPowerMetering")

                if dc_local_dict != dc_dict:
                    consistent = False
                    print("Inconsistency!\n\n")
                    print(f"   Local: {dc_local_dict}")
                    print(f"   Global: {dc_dict}")
                    diff = DeepDiff(dc_local_dict, dc_dict)
                    print("\n\nDiff:")
                    print(diff)
            if not consistent:
                raise DcError(
                    f"local and global data channels for {self.alias} do not match"
                )

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
                or ("report" in fn.type_name)
                or ("snapshot" in fn.type_name)
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
                    if self.alias == "beech":
                        t = beech_br_from_status(t, fn)
                    elif self.alias == "oak":
                        t = oak_br_from_status(t, fn)

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

    if isinstance(t, GridworksEventReport):
        return gridworks_event_report_to_msg(t, fn)
    elif isinstance(t, BatchedReadings):
        return batchedreading_to_msg(t, fn)
    elif isinstance(t, PowerWatts):
        return basic_to_msg(t, fn)
    elif isinstance(t, KeyparamChangeLog):
        return basic_to_msg(t, fn)
    elif isinstance(t, GridworksEventGtShStatus):
        return gridworkseventgtshstatus_to_msg(t, fn)
    else:
        return None


def gridworks_event_report_to_msg(
    t: GridworksEventReport, fn: FileNameMeta
) -> Optional[Message]:
    if (
        t.report.channel_reading_list == []
        and t.report.fsm_action_list == []
        and t.report.fsm_report_list == []
    ):
        return None
    else:
        return Message(
            message_id=t.report.id,
            from_alias=t.report.from_g_node_alias,
            message_persisted_ms=fn.message_persisted_ms,
            payload=t.report.to_dict(),
            message_type_name=t.report.type_name,
            message_created_ms=t.report.message_created_ms,
        )


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
