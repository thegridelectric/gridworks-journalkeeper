import json
import math
from typing import List

import dotenv
import pendulum
from gw.errors import GwTypeError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gwp.back_office_hack import gni_from_alias
from gwp.back_office_hack import ta_from_alias
from gwp.config import Settings
from gwp.enums import TelemetryName
from gwp.first_season.beech_channels import BEECH_CHANNELS_BY_NAME
from gwp.first_season.beech_channels import BcName
from gwp.first_season.beech_channels import BeechAliasMapper
from gwp.first_season.utils import str_from_ms
from gwp.models import Message
from gwp.models import MessageSql
from gwp.models import bulk_insert_idempotent
from gwp.persister_hack import FileNameMeta
from gwp.persister_hack import PersisterHack
from gwp.types import BatchedReadings
from gwp.types import ChannelReadings
from gwp.types import GridworksEventGtShStatus
from gwp.types import GtShStatus_Maker
from gwp.types import KeyparamChangeLog_Maker
from gwp.types import PowerWatts_Maker
from gwp.types import get_tuple_from_type
from gwp.types.base_asl_types import TypeMakerByName


BEECH_IGNORED_ALIASES = [
    "a.elt1",
    "george.special.temp.depth1",
    "george.special.temp.depth2",
    "george.special.temp.depth3",
    "george.special.temp.depth4",
    "a.m.tank1.power",
]

TN_GOOFS = [
    [BcName.OAT, TelemetryName.WaterTempCTimes1000],
    [BcName.DOWN_ZONE_GW_TEMP, TelemetryName.WaterTempCTimes1000],
    [BcName.DOWN_ZONE_TEMP, TelemetryName.WaterTempCTimes1000],
    [BcName.DOWN_ZONE_TEMP, TelemetryName.WaterTempFTimes1000],
    [BcName.DOWN_ZONE_SET, TelemetryName.WaterTempCTimes1000],
    [BcName.DOWN_ZONE_SET, TelemetryName.WaterTempFTimes1000],
    [BcName.UP_ZONE_TEMP, TelemetryName.WaterTempCTimes1000],
    [BcName.UP_ZONE_TEMP, TelemetryName.WaterTempFTimes1000],
    [BcName.UP_ZONE_SET, TelemetryName.WaterTempCTimes1000],
    [BcName.UP_ZONE_SET, TelemetryName.WaterTempFTimes1000],
]


def beech_br_from_status(
    status_event: GridworksEventGtShStatus, fn: FileNameMeta
) -> BatchedReadings:
    """
    Given a GridWorksEventGtShStatus reported by the beech scada,
    returns the equivalent BatchedReading that uses the correct
    beech data channels

    Raises an error if the status doesn't come from beech

    Also raises errors when the new and unknown aliases show up
    for ShNodes

    """
    channel_list = []
    channel_reading_list = []
    status = status_event.status
    if "beech" not in status.from_g_node_alias:
        raise Exception(
            f"supposed to be a beech status. But msg is from {status.about_g_node_alias}"
        )

    simple_list = status.simple_telemetry_list
    for simple in simple_list:
        if not simple.sh_node_alias in BEECH_IGNORED_ALIASES:
            try:
                channel_name = BeechAliasMapper.lookup_name(
                    simple.sh_node_alias, status.slot_start_unix_s
                )
            except ValueError as e:
                raise Exception(
                    f'NEW ALIAS. Add ({status.slot_start_unix_s}, "{simple.sh_node_alias}") to appropriate BeechAliasMapper.channel_mappings'
                )
            channel = BEECH_CHANNELS_BY_NAME[channel_name]
            try:
                assert channel.telemetry_name == simple.telemetry_name
            except:
                if [channel_name, simple.telemetry_name] not in TN_GOOFS:
                    raise Exception(
                        f"{simple.sh_node_alias} had mislabeled {simple.telemetry_name} ... change to {channel.telemetry_name}"
                    )
            channel_list.append(channel)
            channel_reading_list.append(
                ChannelReadings(
                    channel_id=channel.id,
                    value_list=simple.value_list,
                    scada_read_time_unix_ms_list=simple.read_time_unix_ms_list,
                )
            )

    multi_list = status.multipurpose_telemetry_list
    for multi in multi_list:
        if not multi.about_node_alias in BEECH_IGNORED_ALIASES:
            try:
                channel_name = BeechAliasMapper.lookup_name(
                    multi.about_node_alias, status.slot_start_unix_s
                )
            except ValueError as e:
                raise Exception(
                    f'NEW ALIAS. Add ({status.slot_start_unix_s}, "{multi.about_node_alias}") to appropriate BeechAliasMapper.channel_mappings'
                    f"FileName {fn.file_name}. Specific problem: <{multi.as_dict()}>"
                )
            channel = BEECH_CHANNELS_BY_NAME[channel_name]
            try:
                assert channel.telemetry_name == multi.telemetry_name
            except:
                if [channel_name, multi.telemetry_name] not in TN_GOOFS:
                    raise Exception(
                        f"{channel_name} had mislabeled {multi.telemetry_name} ... add  [{channel_name}, {multi.telemetry_name}] to  TN_GOOFS"
                        f"time {str_from_ms(status.slot_start_unix_s * 1000)} America/NY"
                    )
            channel_list.append(channel)
            channel_reading_list.append(
                ChannelReadings(
                    channel_id=channel.id,
                    value_list=multi.value_list,
                    scada_read_time_unix_ms_list=multi.read_time_unix_ms_list,
                )
            )
    return BatchedReadings(
        from_g_node_alias=status.from_g_node_alias,
        from_g_node_instance_id=gni_from_alias(status.from_g_node_alias),
        about_g_node_alias=ta_from_alias(status.from_g_node_alias),
        slot_start_unix_s=status.slot_start_unix_s,
        batched_transmission_period_s=status.reporting_period_s,
        message_created_ms=int(status_event.time_n_s / 10**6),
        data_channel_list=channel_list,
        channel_reading_list=channel_reading_list,
        fsm_action_list=[],
        fsm_report_list=[],
        id=status.status_uid,
    )


def load_beech_batches(p: PersisterHack, start_s: int, duration_hrs: int):
    date_list = p.get_date_folder_list(start_s, duration_hrs)
    print(f"Loading filenames from folders {date_list}")
    fn_list: List[FileNameMeta] = p.get_file_name_meta_list(date_list)

    start_ms = start_s * 1000
    end_ms = (start_s + duration_hrs * 3600) * 1000 + 400
    blist: List[FileNameMeta] = [
        fn
        for fn in fn_list
        if (
            ("status" in fn.type_name)
            or ("power.watts" in fn.type_name)
            or ("keyparam.change.log" in fn.type_name)
        )
        and ("beech" in fn.from_alias)
        and (start_ms <= fn.message_persisted_ms < end_ms)
    ]

    blist.sort(key=lambda x: x.message_persisted_ms)
    print(f"total filenames: {len(blist)}")
    print(
        f"First file persisted {str_from_ms(blist[0].message_persisted_ms)} America/NY"
    )
    print(
        f"Last file persisted at {str_from_ms(blist[-1].message_persisted_ms)} America/NY"
    )

    settings = Settings(_env_file=dotenv.find_dotenv())
    engine = create_engine(settings.db_url.get_secret_value())
    Session = sessionmaker(bind=engine)
    session = Session()

    for i in range(math.ceil(len(blist) / 100)):
        first = blist[i * 100]
        print(
            f"loading messages {i*100} - {i*100+100} [{str_from_ms(first.message_persisted_ms)} America/NY]"
        )

        messages: List[Message] = []
        blank_statuses = 0
        for fn in blist[i * 100 : i * 100 + 100]:
            # get the serialized byte string
            msg_bytes = p.get_message_bytes(fn)
            t = get_tuple_from_type(msg_bytes)

            # Transform status messages into BatchedReadings
            if isinstance(t, GridworksEventGtShStatus):
                t = beech_br_from_status(t, fn)

            # msg may be None if not something we are tracking (comms stuff), or
            # if it is a status message with no data readings
            msg = p.tuple_to_msg(t, fn)
            if msg:
                messages.append(msg)
            else:
                if t.type_name == "batched.readings":
                    blank_statuses += 1

        print(f"For messages {i*100} - {i*100+100}: {blank_statuses} blanks")
        msg_sql_list = list(map(lambda x: x.as_sql(), messages))
        bulk_insert_idempotent(session, msg_sql_list)
        session.commit()
