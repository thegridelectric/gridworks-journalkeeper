import typing
from typing import List, Optional

import boto3
import pendulum
from gwatn.csv_makers import csv_utils
from gwatn.csv_makers.codec import S3MQTTCodec
from gwatn.csv_makers.csv_utils import ChannelReading
from gwproto import Message
from pydantic import BaseModel

REPORT_TYPE_NAME = "scada.report.a.001"
OUT_STUB = "/home/ubuntu/gdrive/MillinocketData/ScadaReportA"
# OUT_STUB = "output_data/scada_report_a"

MIN_FLOW_CALC_SECONDS = 30

DOWNLOADED_FILE_TYPES = [
    GtDispatchBoolean_Maker.type_name,
    GtShStatus_Maker.type_name,
    SnapshotSpaceheat_Maker.type_name,
    GtTelemetry_Maker.type_name,
    SnapshotSpaceheatEvent.__fields__["TypeName"].default,
    GtShStatusEvent.__fields__["TypeName"].default,
]


class FileNameMeta(BaseModel):
    FromGNodeAlias: str
    PayloadTypeName: str
    UnixTimeMs: int
    FileName: str
    TypeName: str = "file.name.meta.000"


def channel_time(reading: ChannelReading) -> str:
    return f"{reading.Channel.DisplayName}_{reading.TimeUnixMs}"


class SnapshotWithSendTime(BaseModel):
    SendTimeUnixMs: int
    Snapshot: SnapshotSpaceheat
    TypeName: str = "wrapped.snapshot.spaceheat.000"


class ScadaReportA_Maker:
    def __init__(self, out_stub=OUT_STUB):
        self.s3 = boto3.client("s3")
        self.aws_bucket_name = "gwdev"
        self.world_instance_name = "hw1__1"
        self.out_stub = f"{out_stub}"
        self.output_type_name = "atn.ui.000"
        self.processed_file_name_meta_list = List[FileNameMeta]
        self.new_file_name_meta_list = List[FileNameMeta]
        self.latest_status_list: List[GtShStatus] = []
        self.latest_snapshot_list: List[SnapshotSpaceheat] = []
        self.latest_dispatch_list: List[GtDispatchBoolean] = []
        self.status_readings_to_write: List[ChannelReading] = []
        self.mqtt_codec = S3MQTTCodec()
        print(f"Initialized {self.__class__}")

    def get_readings_from_dispatch_cmds(
        self,
        payload: GtDispatchBoolean,
        atn_alias: str,
    ) -> List[ChannelReading]:
        channel = csv_utils.get_channel(
            atn_alias=atn_alias,
            from_name=payload.FromGNodeAlias,
            about_name=payload.AboutNodeName,
            telemetry_name=TelemetryName.RelayState,
        )
        return [
            ChannelReading(
                Channel=channel,
                TimeUnixMs=payload.SendTimeUnixMs,
                IntValue=payload.RelayState,
            )
        ]

    def get_readings_from_snapshot_messages(
        self, payload: SnapshotSpaceheatEvent, atn_alias: str
    ) -> List[ChannelReading]:
        readings = []
        snapshot = payload.snap.Snapshot

        time_unix_ms = snapshot.ReportTimeUnixMs
        tns_to_use = [TelemetryName.RelayState, TelemetryName.PowerW]
        for i in range(len(snapshot.ValueList)):
            tn = snapshot.TelemetryNameList[i]
            if tn in tns_to_use:
                if tn == TelemetryName.RelayState:
                    channel = csv_utils.get_channel(
                        atn_alias=atn_alias,
                        from_name=snapshot.AboutNodeAliasList[i],
                        about_name=snapshot.AboutNodeAliasList[i],
                        telemetry_name=snapshot.TelemetryNameList[i],
                    )
                else:
                    # WARNING: a.m should be replaced by the scada's power meter
                    # but this requires access to the hardware layout
                    channel = csv_utils.get_channel(
                        atn_alias=atn_alias,
                        from_name="a.m",
                        about_name=snapshot.AboutNodeAliasList[i],
                        telemetry_name=snapshot.TelemetryNameList[i],
                    )
                reading = ChannelReading(
                    Channel=channel,
                    TimeUnixMs=time_unix_ms,
                    IntValue=snapshot.ValueList[i],
                )
                readings.append(reading)
        return readings

    def get_readings_from_status_messages(
        self, payload: GtShStatusEvent, atn_alias: str
    ) -> List[ChannelReading]:
        status = payload.status
        if isinstance(status, dict):
            status = GtShStatus(**status)
        readings: List[ChannelReading] = []
        for single in status.SimpleTelemetryList:
            for i in range(len(single.ValueList)):
                channel = csv_utils.get_channel(
                    atn_alias=atn_alias,
                    from_name=single.ShNodeAlias,
                    about_name=single.ShNodeAlias,
                    telemetry_name=single.TelemetryName,
                )
                reading = ChannelReading(
                    Channel=channel,
                    TimeUnixMs=single.ReadTimeUnixMsList[i],
                    IntValue=single.ValueList[i],
                )
                readings.append(reading)

        for cmd in status.BooleanactuatorCmdList:
            for i in range(len(cmd.RelayStateCommandList)):
                channel = csv_utils.get_channel(
                    atn_alias=atn_alias,
                    from_name="a.s",
                    about_name=cmd.ShNodeAlias,
                    telemetry_name=TelemetryName.RelayState,
                )
                reading = ChannelReading(
                    Channel=channel,
                    TimeUnixMs=cmd.CommandTimeUnixMsList[i],
                    IntValue=cmd.RelayStateCommandList[i],
                )
                readings.append(reading)

        for multi in status.MultipurposeTelemetryList:
            for i in range(len(multi.ValueList)):
                channel = csv_utils.get_channel(
                    atn_alias=atn_alias,
                    from_name=multi.SensorNodeAlias,
                    about_name=multi.AboutNodeAlias,
                    telemetry_name=multi.TelemetryName,
                )
                reading = ChannelReading(
                    Channel=channel,
                    TimeUnixMs=multi.ReadTimeUnixMsList[i],
                    IntValue=multi.ValueList[i],
                )
                readings.append(reading)
        return readings

    def get_message_bytes(self, file_name_meta: FileNameMeta) -> bytes:
        s3_object = self.s3.get_object(
            Bucket=self.aws_bucket_name, Key=file_name_meta.FileName
        )
        msg_as_bytes = s3_object["Body"].read()
        return msg_as_bytes

    def has_this_days_folder(self, time_s: int) -> bool:
        d = pendulum.from_timestamp(time_s)
        this_days_folder_name = d.strftime("%Y%m%d")
        prefix = f"{self.world_instance_name}/eventstore/{this_days_folder_name}"

        r = self.s3.list_objects_v2(Bucket=self.aws_bucket_name, Prefix=prefix)
        if "Contents" in r.keys():
            return True
        return False

    def get_date_folder_list(
        self, start_time_unix_ms: int, duration_hrs: int
    ) -> List[str]:
        start_s = start_time_unix_ms / 1000
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

    def get_file_name_meta_list(
        self,
        start_time_unix_ms: int,
        end_time_unix_ms: int,
        date_folder_list: List[str],
        g_node_alias_list: List[str],
        type_name_list: Optional[List[str]] = None,
    ):
        if type_name_list is None:
            type_name_list = DOWNLOADED_FILE_TYPES
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
                    from_g_node_alias = file_name.split("/")[-1].split("-")[0]
                    payload_type_name = file_name.split("/")[-1].split("-")[1]
                    payload_unix_time_ms = int(file_name.split("/")[-1].split("-")[2])
                except:
                    raise Exception(f"Failed file name parsing with {file_name}")

                if (
                    from_g_node_alias in g_node_alias_list
                    and payload_type_name in type_name_list
                    and payload_unix_time_ms > start_time_unix_ms - 300_000
                    and payload_unix_time_ms < end_time_unix_ms + 600_000
                ):
                    fn_list.append(
                        FileNameMeta(
                            FromGNodeAlias=from_g_node_alias,
                            PayloadTypeName=payload_type_name,
                            UnixTimeMs=payload_unix_time_ms,
                            FileName=file_name,
                        )
                    )

        return fn_list

    def get_readings(
        self, start_time_unix_ms: int, duration_hrs: int, atn_alias: str
    ) -> List[ChannelReading]:
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

        readings: List[ChannelReading] = []
        for i in range(len(fn_list)):
            fn = fn_list[i]
            message_bytes = self.get_message_bytes(fn)
            kafka_topic = csv_utils.kafka_topic_from_s3_filename(fn.FileName)
            type_name = csv_utils.type_name_from_kafka_topic(kafka_topic)

            # TODO: add gw to kafka topics where message_bytes TypeName is gw, and
            # the type_name refers to the Payload

            message = typing.cast(Message, self.mqtt_codec.decode("gw", message_bytes))
            match message.Payload:
                case GtDispatchBoolean():
                    readings += self.get_readings_from_dispatch_cmds(
                        message.Payload, atn_alias
                    )
                case GtShStatusEvent():
                    readings += self.get_readings_from_status_messages(
                        message.Payload, atn_alias
                    )
                case SnapshotSpaceheatEvent():
                    readings += self.get_readings_from_snapshot_messages(
                        message.Payload, atn_alias
                    )
        channels = list(set(map(lambda x: x.Channel, readings)))
        gallon_channels = list(
            filter(lambda x: x.TelemetryName == TelemetryName.GallonsTimes100, channels)
        )
        for gallon_ch in gallon_channels:
            gallon_readings = sorted(
                list(filter(lambda x: x.Channel == gallon_ch, readings)),
                key=lambda reading: channel_time(reading),
            )
            readings += csv_utils.get_flow_readings(
                gallon_readings=gallon_readings,
                gallon_ch=gallon_ch,
                atn_alias=atn_alias,
                add_smoothing=True,
            )
        return readings

    def make_csv(
        self,
        start_s,
        duration_hrs: int = 48,
        atn_alias: str = "hw1.isone.ct.newhaven.orange1",
    ):
        s = start_s - (start_s % 3600)
        start_time_utc = pendulum.from_timestamp(s)
        print(f"starting at {start_time_utc.strftime('%Y-%m-%d %H:%M')}")
        start_time_unix_ms = s * 1000

        readings = self.get_readings(
            start_time_unix_ms=start_time_unix_ms,
            duration_hrs=duration_hrs,
            atn_alias=atn_alias,
        )
        sorted_readings = sorted(readings, key=lambda reading: channel_time(reading))
        lines = [
            f"AtomicTNode:, {atn_alias}\n",
            "ReportTypeName:, scada.report.a.001\n"
            "Channel&Time, TimeUtc, Channel, TimeUnixMs, Value, TelemetryName, AboutShNode, FromShNode\n",
        ]
        for reading in sorted_readings:
            time_utc_str = pendulum.from_timestamp(reading.TimeUnixMs / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            line = f"{channel_time(reading)},{time_utc_str},{reading.Channel.DisplayName}, {reading.TimeUnixMs}"
            value = reading.IntValue
            if reading.FloatValue is not None:
                value = reading.FloatValue
            line += f",{value}"
            line += f", {reading.Channel.TelemetryName.value}"
            line += f", {reading.Channel.AboutName}"
            line += f", {reading.Channel.FromName}\n"
            lines.append(line)

        atn_end = atn_alias.split(".")[-1]
        file_name = f"{self.out_stub}/{atn_end}-{start_time_utc.strftime('%Y%m%d-%H%M')}-{duration_hrs}-{atn_alias}-{REPORT_TYPE_NAME}.csv"
        print(f"Writing {file_name}")
        with open(file_name, "w") as outfile:
            outfile.writelines(lines)
