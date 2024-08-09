import math
from typing import List

import dotenv
from gjk.back_office_hack import gni_from_alias, ta_from_alias
from gjk.codec import deserialize
from gjk.config import Settings
from gjk.enums import TelemetryName
from gjk.first_season.beech_channels import (
    BEECH_CHANNELS_BY_NAME,
    BcName,
    BeechAliasMapper,
)
from gjk.first_season.utils import str_from_ms
from gjk.journal_keeper_hack import FileNameMeta, JournalKeeperHack
from gjk.models import bulk_insert_messages
from gjk.type_helpers import Message
from gjk.types import (
    BatchedReadings,
    ChannelReadings,
    GridworksEventGtShStatus,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BEECH_IGNORED_ALIASES = [
    "a.elt1",
    "george.special.temp.depth1",
    "george.special.temp.depth2",
    "george.special.temp.depth3",
    "george.special.temp.depth4",
    "a.m.tank1.power",
    "a.m.tank2.power",
    "a.m.tank3.power",
    "calibrate.1009.temp.depth1",
    "calibrate.1009.temp.depth2",
    "calibrate.1009.temp.depth3",
    "calibrate.1009.temp.depth4",
]

TN_GOOFS = [
    [BcName.OAT, TelemetryName.WaterTempCTimes1000],
    [BcName.OAT, TelemetryName.AirTempFTimes1000],
    [BcName.DOWN_ZONE_GW_TEMP, TelemetryName.WaterTempCTimes1000],
    [BcName.DOWN_ZONE_TEMP, TelemetryName.WaterTempCTimes1000],
    [BcName.DOWN_ZONE_TEMP, TelemetryName.WaterTempFTimes1000],
    [BcName.DOWN_ZONE_TEMP, TelemetryName.AirTempCTimes1000],
    [BcName.DOWN_ZONE_SET, TelemetryName.WaterTempCTimes1000],
    [BcName.DOWN_ZONE_SET, TelemetryName.WaterTempFTimes1000],
    [BcName.DOWN_ZONE_SET, TelemetryName.AirTempCTimes1000],
    [BcName.UP_ZONE_TEMP, TelemetryName.WaterTempCTimes1000],
    [BcName.UP_ZONE_TEMP, TelemetryName.WaterTempFTimes1000],
    [BcName.UP_ZONE_TEMP, TelemetryName.AirTempCTimes1000],
    [BcName.UP_ZONE_SET, TelemetryName.WaterTempCTimes1000],
    [BcName.UP_ZONE_SET, TelemetryName.WaterTempFTimes1000],
    [BcName.UP_ZONE_SET, TelemetryName.AirTempCTimes1000],
    [BcName.UP_ZONE_GW_TEMP, TelemetryName.WaterTempCTimes1000],
    [BcName.UP_ZONE_GW_TEMP, TelemetryName.AirTempFTimes1000],
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

    If there is an error in making BatchedReadings it returns the original status_event

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
        if simple.sh_node_alias not in BEECH_IGNORED_ALIASES:
            try:
                channel_name = BeechAliasMapper.lookup_name(
                    simple.sh_node_alias, status.slot_start_unix_s
                )
            except ValueError as e:
                raise Exception(
                    f'NEW ALIAS. Add ({status.slot_start_unix_s}, "{simple.sh_node_alias}") to appropriate BeechAliasMapper.channel_mappings'
                ) from e
            channel = BEECH_CHANNELS_BY_NAME[channel_name]
            try:
                assert channel.telemetry_name == simple.telemetry_name
            except Exception as e:
                if [channel_name, simple.telemetry_name] not in TN_GOOFS:
                    raise Exception(
                        f"{simple.sh_node_alias} had mislabeled {simple.telemetry_name} ... change to {channel.telemetry_name}"
                    ) from e
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
        if multi.about_node_alias not in BEECH_IGNORED_ALIASES:
            try:
                channel_name = BeechAliasMapper.lookup_name(
                    multi.about_node_alias, status.slot_start_unix_s
                )
            except ValueError as e:
                raise Exception(
                    f'NEW ALIAS. Add ({status.slot_start_unix_s}, "{multi.about_node_alias}") to appropriate BeechAliasMapper.channel_mappings'
                    f"FileName {fn.file_name}. Specific problem: <{multi.as_dict()}>"
                ) from e
            channel = BEECH_CHANNELS_BY_NAME[channel_name]
            try:
                assert channel.telemetry_name == multi.telemetry_name
            except Exception as e:
                if [channel_name, multi.telemetry_name] not in TN_GOOFS:
                    raise Exception(
                        f"{fn.file_name}: "
                        f"{channel_name} had mislabeled {multi.telemetry_name} ... add  [{channel_name}, {multi.telemetry_name}] to  TN_GOOFS"
                        f"time {str_from_ms(status.slot_start_unix_s * 1000)} America/NY"
                    ) from e
            channel_list.append(channel)
            channel_reading_list.append(
                ChannelReadings(
                    channel_id=channel.id,
                    value_list=multi.value_list,
                    scada_read_time_unix_ms_list=multi.read_time_unix_ms_list,
                )
            )

    try:
        return_tuple = BatchedReadings(
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
    except Exception as e:
        print("STORING AS GridworksEventGtShStatus")
        print(f"Examine {fn.file_name} for error: \n: <{e}>.")
        return_tuple = status_event
    return return_tuple


def load_beech_batches(p: JournalKeeperHack, start_s: int, duration_hrs: int):
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
            f"loading messages {i * 100} - {i * 100 + 100} [{str_from_ms(first.message_persisted_ms)} America/NY]"
        )

        messages: List[Message] = []
        blank_statuses = 0
        for fn in blist[i * 100 : i * 100 + 100]:
            # get the serialized byte string
            msg_bytes = p.get_message_bytes(fn)
            if fn.type_name == "keyparam.change.log":
                # Something hinky in the coding of these messages, which
                # I sent via mosquitto_pub.
                # It had an extra b:
                # b'b{"AboutNodeAlias": "beech"}'
                print(f"Got {fn.file_name}!")
                json_str = msg_bytes.decode("utf-8")[1:]
                msg_bytes = json_str.encode("utf-8")

            try:
                t = deserialize(msg_bytes)
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
                msg = p.tuple_to_msg(t, fn)
            except Exception as e:
                print(f"Problem with {fn.file_name}: {e}")
            if msg:
                messages.append(msg)
            elif t.type_name == "batched.readings":
                blank_statuses += 1

        print(f"For messages {i * 100} - {i * 100 + 100}: {blank_statuses} blanks")
        msg_sql_list = list(map(lambda x: x.as_sql(), messages))
        bulk_insert_messages(session, msg_sql_list)
        session.commit()
