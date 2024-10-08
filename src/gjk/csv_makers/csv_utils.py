from typing import List, Optional

from gwatn.enums import TelemetryName
from gwatn.types.data_channel import DataChannel
from pydantic import BaseModel

APPLE_ATN_ALIAS = "hw1.isone.me.freedom.apple"
ORANGE_ATN_ALIAS = "hw1.isone.ct.newhaven.orange1"


class ChannelReading(BaseModel):
    Channel: DataChannel
    TimeUnixMs: int
    IntValue: Optional[int]
    FloatValue: Optional[float]
    TypeName: str = "channel.reading.000"


def get_named_channels(
    atn_alias: str = "hw1.isone.me.freedom.apple",
) -> List[DataChannel]:
    # TODO: replace when DataChannels exist in db in a way that
    # is uniquely referenced by the Atn
    scada_alias = atn_alias + ".scada"
    channels: List[DataChannel] = []
    if atn_alias == APPLE_ATN_ALIAS:
        channels.append(
            DataChannel(
                DisplayName="Buffer_Out_Temp",
                AboutName="a.buffer.out.temp",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Dist_Pump_Power",
                AboutName="a.distsourcewater.pump",
                FromName="a.m",
                TelemetryName=TelemetryName.PowerW,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Dist_RWT",
                AboutName="a.distreturnwater.temp",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Dist_Gallons",
                AboutName="a.distsourcewater.pump.flowmeter",
                FromName="a.distsourcewater.pump.flowmeter",
                TelemetryName=TelemetryName.GallonsTimes100,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Dist_Gpm",
                AboutName="a.distsourcewater.pump.flowmeter",
                FromName="derived.gpm.expsmooth.000",
                TelemetryName=TelemetryName.GpmTimes100,
                ExpectedMaxValue=600,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Dist_SWT",
                AboutName="a.distsourcewater.temp",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Heatpump_Power",
                AboutName="a.heatpump",
                FromName="a.m",
                TelemetryName=TelemetryName.PowerW,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Glycol_RWT",
                AboutName="a.heatpump.condensorloopreturn.temp",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Glycol_Pump_Power",
                AboutName="a.heatpump.condensorloopsource.pump",
                FromName="a.m",
                TelemetryName=TelemetryName.PowerW,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Glycol_Gallons",
                AboutName="a.heatpump.condensorloopsource.pump.flowmeter",
                FromName="a.heatpump.condensorloopsource.pump.flowmeter",
                TelemetryName=TelemetryName.GallonsTimes100,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Glycol_Gpm",
                AboutName="a.heatpump.condensorloopsource.pump.flowmeter",
                FromName="derived.gpm.expsmooth.000",
                TelemetryName=TelemetryName.GpmTimes100,
                ExpectedMaxValue=600,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Glycol_SWT",
                AboutName="a.heatpump.condensorloopsource.temp",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="HotStoreIn_Temp",
                AboutName="a.hotstore.in.temp",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="HotStoreOut_Gallons",
                AboutName="a.hotstore.out.flowmeter",
                FromName="a.hotstore.out.flowmeter",
                TelemetryName=TelemetryName.GallonsTimes100,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="HotStoreOut_Gpm",
                AboutName="a.hotstore.out.flowmeter",
                FromName="derived.gpm.expsmooth.000",
                TelemetryName=TelemetryName.GpmTimes100,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="HotStoreOut_Temp",
                AboutName="a.hotstore.out.temp",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Hx_Pump_Power",
                AboutName="a.hxpump",
                FromName="a.m",
                TelemetryName=TelemetryName.PowerW,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Outside_Temp",
                AboutName="a.outside",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Tank1_Elements_Atn_Dispatch",
                AboutName="a.tank1.elts.relay",
                FromName="hw1.isone.me.freedom.apple",
                TelemetryName=TelemetryName.RelayState,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Tank1_Elements_SCADA_Dispatch",
                AboutName="a.tank1.elts.relay",
                FromName="a.s",
                TelemetryName=TelemetryName.RelayState,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Tank1_Elements_Relay",
                AboutName="a.tank1.elts.relay",
                FromName="a.tank1.elts.relay",
                TelemetryName=TelemetryName.RelayState,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Tank1_Elements_Power",
                AboutName="a.tank1.elts",
                FromName="a.m",
                TelemetryName=TelemetryName.PowerW,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Tank1_Temp1",
                AboutName="a.tank1.temp1",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Tank1_Temp2",
                AboutName="a.tank1.temp2",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
        channels.append(
            DataChannel(
                DisplayName="Tank1_Temp3",
                AboutName="a.tank1.temp3",
                FromName="a.s.analog.temp",
                TelemetryName=TelemetryName.WaterTempCTimes1000,
            )
        )
    return channels


def get_channel(
    atn_alias: str,
    from_name: str,
    about_name: str,
    telemetry_name: TelemetryName,
) -> DataChannel:
    if not isinstance(telemetry_name, TelemetryName):
        raise Exception(
            f"Error with from_name {from_name}, about_name {about_name}, telemetry_name {telemetry_name}"
        )
    named_channels = get_named_channels(atn_alias)
    this_channel_list = list(
        filter(
            lambda x: x.FromName == from_name
            and x.AboutName == about_name
            and x.TelemetryName == telemetry_name,
            named_channels,
        )
    )
    if len(this_channel_list) == 0:
        display_name = f"{about_name}_{telemetry_name.value}_{from_name}"
        return DataChannel(
            DisplayName=display_name,
            AboutName=about_name,
            FromName=from_name,
            TelemetryName=telemetry_name,
        )

    elif len(this_channel_list) == 1:
        return this_channel_list[0]
    else:
        raise Exception(f"duplicate channels {this_channel_list}")


def from_g_node_alias_from_kafka_topic(kafka_topic: str) -> str:
    try:
        from_alias = kafka_topic.split("-")[0]
    except:
        raise Exception("Failure getting from g node alias from kafka topic")
    return from_alias


def type_name_from_kafka_topic(kafka_topic: str) -> str:
    """
    Returns the type name from the kafka topic
    Args:
        kafka_topic (str):

    Returns:
        type_name
    """
    try:
        type_name = kafka_topic.split("-")[1]
    except:
        raise Exception("Failure getting type name from kafka topic")
    return type_name


def kafka_topic_from_s3_filename(s3_filename: str) -> str:
    try:
        topic = "-".join(s3_filename.split("/")[3].split("-")[0:2])
    except:
        raise Exception("Failure getting kafka topic from type name")
    return topic


def get_flow_readings(
    gallon_readings: List[ChannelReading],
    gallon_ch: DataChannel,
    atn_alias: str,
    add_smoothing: bool = False,
    exp_minute_weight: float = 0.5,
) -> List[ChannelReading]:
    """
    This function applies the `derived.gpm.simple.000` or `derived.gpm.expsmooth.000` transformation,
    depending on whether add_smoothin is true or false

    It takes as input a DataChannel (and related readings) whose TelemetryName is GallonsTimes100,
    and returns a DataChannel whose source is derived.gpm.expsmooth.000, whose TelemetryName is
    GallonsGpm

    Args:
        gallon_readings:
        gallon_ch:

    Returns:
        List of channel readings (todo: turn this into an object, so it doesn't have to repeat the DataChannel
        in each individual reading)

    Raises: exception if the inbound Telemetry is not GallonsTimes100 or if AboutName = FromName
    for inbound DataChannel
    """
    if add_smoothing:
        transform_name = "derived.gpm.expsmooth.000"
    else:
        transform_name = "derived.gpm.simple.000"
    MIN_FLOW_CALC_SECONDS = 30
    DELTA_MAX_TRIGGER = 0.2
    if gallon_ch.TelemetryName != TelemetryName.GallonsTimes100:
        raise Exception(
            "get_flow_reading requires an input DataChannel in GallonsTimes100!"
        )

    if gallon_ch.AboutName != gallon_ch.FromName:
        raise Exception(
            "get_flow_reading requires an input DataChannel of raw data created"
            "directly by the channel itself (i.e. AboutName = FromName)"
        )

    flow_channel = get_channel(
        atn_alias=atn_alias,
        about_name=gallon_ch.AboutName,
        from_name=transform_name,
        telemetry_name=TelemetryName.GpmTimes100,
    )

    new_readings = []
    prev_idx = 0
    prev_reading = gallon_readings[0]
    prev_time_s = prev_reading.TimeUnixMs / 1000
    prev_flow_gpm: Optional[float] = None
    idx = 1
    while idx < len(gallon_readings):
        time_s = gallon_readings[idx].TimeUnixMs / 1000
        while (time_s - prev_time_s < MIN_FLOW_CALC_SECONDS) and idx < (
            len(gallon_readings) - 1
        ):
            idx += 1
            time_s = gallon_readings[idx].TimeUnixMs / 1000
        prev_gallons_times_100 = gallon_readings[prev_idx].IntValue
        this_gallons_times_100 = gallon_readings[idx].IntValue
        delta_gallons = (this_gallons_times_100 - prev_gallons_times_100) / 100
        delta_min = (time_s - prev_time_s) / 60

        latest_flow_gpm = delta_gallons / delta_min
        flow_gpm = latest_flow_gpm
        if prev_flow_gpm is not None and flow_channel.ExpectedMaxValue is not None:
            if flow_channel.ExpectedMaxValue == 0:
                raise Exception(
                    f"Flow Channel {flow_channel} has an ExpectedMaxValue of 0 - should not happen"
                )
            expected_max_gpm = flow_channel.ExpectedMaxValue / 100
            if abs((flow_gpm - prev_flow_gpm) / expected_max_gpm) < DELTA_MAX_TRIGGER:
                alpha = exp_minute_weight * delta_min
                flow_gpm = alpha * latest_flow_gpm + (1 - alpha) * prev_flow_gpm

        new_readings.append(
            ChannelReading(
                Channel=flow_channel,
                TimeUnixMs=gallon_readings[idx].TimeUnixMs,
                IntValue=int(flow_gpm * 100),
            )
        )
        prev_time_s = time_s
        prev_flow_gpm = flow_gpm
        prev_idx = idx
        idx += 1

    return new_readings
