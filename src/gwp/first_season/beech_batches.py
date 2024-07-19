import json
from typing import List

import dotenv
import pendulum
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gwp.back_office_hack import gni_from_alias
from gwp.back_office_hack import ta_from_alias
from gwp.config import Settings
from gwp.enums import TelemetryName
from gwp.first_season.beech_batches import batched_reading_from_status
from gwp.first_season.beech_channels import BEECH_CHANNELS_BY_NAME
from gwp.first_season.beech_channels import BcName
from gwp.first_season.beech_channels import BeechAliasMapper
from gwp.models import Message
from gwp.models import MessageSql
from gwp.models import bulk_insert_idempotent
from gwp.persister_hack import FileNameMeta
from gwp.persister_hack import PersisterHack
from gwp.types import BatchedReadings
from gwp.types import ChannelReadings
from gwp.types import GridworksEventGtShStatus_Maker as Maker
from gwp.types import GtShStatus


BEECH_IGNORED_ALIASES = ["a.elt1"]
TN_GOOFS = [[BcName.OAT, TelemetryName.WaterTempCTimes1000]]


def batched_reading_from_status(status: GtShStatus) -> BatchedReadings:
    channel_list = []
    channel_reading_list = []

    simple_list = status.simple_telemetry_list
    for simple in simple_list:
        if not simple.sh_node_alias in BEECH_IGNORED_ALIASES:
            try:
                channel_name = BeechAliasMapper.lookup_name(
                    simple.sh_node_alias, status.slot_start_unix_s
                )
            except ValueError as e:
                raise Exception(
                    f"No mapping to channel for {simple.sh_node_alias} at {status.slot_start_unix_s}"
                )
            channel = BEECH_CHANNELS_BY_NAME[channel_name]
            try:
                assert channel.telemetry_name == simple.telemetry_name
            except:
                if [channel_name, simple.telemetry_name] not in TN_GOOFS:
                    raise Exception(
                        f"{simple.sh_node_alias} had mislabled {simple.telemetry_name} ... change to {channel.telemetry_name}"
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
                    f"No mapping to channel for {multi.about_node_alias} at {status.slot_start_unix_s}"
                )
            channel = BEECH_CHANNELS_BY_NAME[channel_name]
            try:
                assert channel.telemetry_name == multi.telemetry_name
            except:
                if [channel_name, multi.telemetry_name] not in TN_GOOFS:
                    raise Exception(
                        f"{multi.about_node_alias} had mislabled {multi.telemetry_name} ... change to {channel.telemetry_name}"
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
        data_channel_list=channel_list,
        channel_reading_list=channel_reading_list,
        fsm_action_list=[],
        fsm_report_list=[],
        id=status.status_uid,
    )


def load_beech_batches(p: PersisterHack, start_s: int, duration_hrs: int):
    date_list = p.get_date_folder_list(start_s, duration_hrs)
    fn_list: List[FileNameMeta] = p.get_file_name_meta_list(date_list)
    # 1 hr ~ 8 seconds

    blist = [
        fn
        for fn in fn_list
        if ("status" in fn.type_name) and ("beech" in fn.from_alias)
    ]

    settings = Settings(_env_file=dotenv.find_dotenv())
    engine = create_engine(settings.db_url.get_secret_value())
    Session = sessionmaker(bind=engine)
    session = Session()

    for i in range(blist / 100):
        print(f"loading messages {i*100} - {i*100+100}")
        messages: List[MessageSql] = []
        blanks = []
        for fn in blist[i * 100 : i * 100 + 100]:
            content = json.loads(p.get_message_bytes(fn).decode("utf-8"))
            d = content["Payload"]
            event = Maker.dict_to_tuple(Maker.first_season_fix(d))
            br = batched_reading_from_status(event.status)

            if br.data_channel_list == []:
                blanks.append(br)
            else:
                messages.append(
                    Message(
                        message_id=br.id,
                        from_alias=br.from_g_node_alias,
                        message_persisted_ms=fn.message_persisted_ms,
                        payload=br.as_dict(),
                        type_name=br.type_name,
                        message_created_ms=int(event.time_n_s / 10**6),
                    )
                )
        print(f"For messages  messages {i*100} - {i*100+100}: {len(blanks)} blanks")
        msg_sql_list = list(map(lambda x: x.as_sql(), messages))
        bulk_insert_idempotent(session, msg_sql_list)
        session.commit()
