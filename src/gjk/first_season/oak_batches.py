from gjk.back_office_hack import gni_from_alias, ta_from_alias
from gjk.enums import TelemetryName
from gjk.first_season.oak_channels import (
    OAK_CHANNELS_BY_NAME,
    OcName,
    OakAliasMapper,
)
from gjk.types import (
    BatchedReadings,
    ChannelReadings,
    GridworksEventGtShStatus,
)
from gjk.utils import FileNameMeta, str_from_ms

OAK_IGNORED_ALIASES = [
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

TN_GOOFS = []
#     [OcName.OAT, TelemetryName.WaterTempCTimes1000],
#     [OcName.OAT, TelemetryName.AirTempFTimes1000],
#     [OcName.DOWN_ZONE_GW_TEMP, TelemetryName.WaterTempCTimes1000],
#     [OcName.DOWN_ZONE_TEMP, TelemetryName.WaterTempCTimes1000],
#     [OcName.DOWN_ZONE_TEMP, TelemetryName.WaterTempFTimes1000],
#     [OcName.DOWN_ZONE_TEMP, TelemetryName.AirTempCTimes1000],
#     [OcName.DOWN_ZONE_SET, TelemetryName.WaterTempCTimes1000],
#     [OcName.DOWN_ZONE_SET, TelemetryName.WaterTempFTimes1000],
#     [OcName.DOWN_ZONE_SET, TelemetryName.AirTempCTimes1000],
#     [OcName.UP_ZONE_TEMP, TelemetryName.WaterTempCTimes1000],
#     [OcName.UP_ZONE_TEMP, TelemetryName.WaterTempFTimes1000],
#     [OcName.UP_ZONE_TEMP, TelemetryName.AirTempCTimes1000],
#     [OcName.UP_ZONE_SET, TelemetryName.WaterTempCTimes1000],
#     [OcName.UP_ZONE_SET, TelemetryName.WaterTempFTimes1000],
#     [OcName.UP_ZONE_SET, TelemetryName.AirTempCTimes1000],
#     [OcName.UP_ZONE_GW_TEMP, TelemetryName.WaterTempCTimes1000],
#     [OcName.UP_ZONE_GW_TEMP, TelemetryName.AirTempFTimes1000],
# ]


def oak_br_from_status(
    status_event: GridworksEventGtShStatus,
    fn: FileNameMeta,
) -> BatchedReadings:
    """
    Given a GridWorksEventGtShStatus reported by the oak scada,
    returns the equivalent BatchedReading that uses the correct
    oak data channels

    Raises an error if the status doesn't come from oak

    Also raises errors when the new and unknown aliases show up
    for ShNodes

    If there is an error in making BatchedReadings it returns the original status_event

    """
    channel_list = []
    channel_reading_list = []
    status = status_event.status
    if "oak" not in status.from_g_node_alias:
        raise Exception(
            f"supposed to be a oak status. But msg is from {status.about_g_node_alias}"
        )

    simple_list = status.simple_telemetry_list
    for simple in simple_list:
        if simple.sh_node_alias not in OAK_IGNORED_ALIASES:
            try:
                channel_name = OakAliasMapper.lookup_name(
                    simple.sh_node_alias, status.slot_start_unix_s
                )
            except ValueError as e:
                raise Exception(
                    f'NEW ALIAS. Add ({status.slot_start_unix_s}, "{simple.sh_node_alias}") to appropriate OakAliasMapper.channel_mappings'
                ) from e
            channel = OAK_CHANNELS_BY_NAME[channel_name]
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
        if multi.about_node_alias not in OAK_IGNORED_ALIASES:
            try:
                channel_name = OakAliasMapper.lookup_name(
                    multi.about_node_alias, status.slot_start_unix_s
                )
            except ValueError as e:
                raise Exception(
                    f'NEW ALIAS. Add ({status.slot_start_unix_s}, "{multi.about_node_alias}") to appropriate OakAliasMapper.channel_mappings'
                    f"FileName {fn.file_name}. Specific problem: <{multi.as_dict()}>"
                ) from e
            channel = OAK_CHANNELS_BY_NAME[channel_name]
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
