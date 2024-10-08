import time
from typing import List, NamedTuple, Optional

import pendulum
import xlsxwriter
from gwatn.csv_makers import csv_utils
from gwatn.csv_makers.csv_utils import ChannelReading
from gwatn.csv_makers.scada_report_a import ScadaReportA_Maker
from gwatn.enums import Unit
from gwatn.types.data_channel import DataChannel
from gwproto.enums import TelemetryName
from pydantic import BaseModel

OUT_STUB = "output_data/freedom_flow"
timezone_string = "US/Eastern"
APPLE_ATN_ALIAS = "hw1.isone.me.freedom.apple"


def c_to_f(temp_c: float) -> float:
    return (temp_c * 1.8) + 32


class RidgelineOutputRow(BaseModel):
    TimeUtc: str
    TimeEastern: str
    DistSwtTempF: Optional[float]
    DistRwtTempF: Optional[float]
    DistFlowGpm: Optional[float]
    GlycolSwtTempF: Optional[float]
    GlycolRwtTempF: Optional[float]
    GlycolFlowGpm: Optional[float]


class RidgelineChannel(NamedTuple):
    Channel: DataChannel
    DaveName: str
    OutUnits: Unit


dist_swt_channel = csv_utils.get_channel(
    atn_alias=APPLE_ATN_ALIAS,
    from_name="a.s.analog.temp",
    about_name="a.distsourcewater.temp",
    telemetry_name=TelemetryName.WaterTempCTimes1000,
)
DIST_SWT = RidgelineChannel(
    Channel=dist_swt_channel, DaveName="Dist SWT", OutUnits=Unit.Fahrenheit
)

dist_rwt_channel = csv_utils.get_channel(
    atn_alias=APPLE_ATN_ALIAS,
    from_name="a.s.analog.temp",
    about_name="a.distreturnwater.temp",
    telemetry_name=TelemetryName.WaterTempCTimes1000,
)
DIST_RWT = RidgelineChannel(
    Channel=dist_rwt_channel,
    DaveName="Dist RWT",
    OutUnits=Unit.Fahrenheit,
)

dist_gpm = csv_utils.get_channel(
    atn_alias=APPLE_ATN_ALIAS,
    from_name="derived.gpm.expsmooth.000",
    about_name="a.distsourcewater.pump.flowmeter",
    telemetry_name=TelemetryName.GpmTimes100,
)
DIST_FLOW = RidgelineChannel(
    Channel=dist_gpm,
    DaveName="Dist Flow",
    OutUnits=Unit.Gpm,
)

glycol_swt_channel = csv_utils.get_channel(
    atn_alias=APPLE_ATN_ALIAS,
    from_name="a.s.analog.temp",
    about_name="a.heatpump.condensorloopsource.temp",
    telemetry_name=TelemetryName.WaterTempCTimes1000,
)

GLYCOL_SWT = RidgelineChannel(
    Channel=glycol_swt_channel,
    DaveName="Glycol SWT",
    OutUnits=Unit.Fahrenheit,
)

glycol_rwt_channel = csv_utils.get_channel(
    atn_alias=APPLE_ATN_ALIAS,
    from_name="a.s.analog.temp",
    about_name="a.heatpump.condensorloopreturn.temp",
    telemetry_name=TelemetryName.WaterTempCTimes1000,
)

GLYCOL_RWT = RidgelineChannel(
    Channel=glycol_rwt_channel,
    DaveName="Glycol RWT",
    OutUnits=Unit.Fahrenheit,
)

glycol_gpm_channel = csv_utils.get_channel(
    atn_alias=APPLE_ATN_ALIAS,
    from_name="derived.gpm.expsmooth.000",
    about_name="a.heatpump.condensorloopsource.pump.flowmeter",
    telemetry_name=TelemetryName.GpmTimes100,
)

GLYCOL_FLOW = RidgelineChannel(
    Channel=glycol_gpm_channel,
    DaveName="Glycol Flow",
    OutUnits=Unit.Gpm,
)


def export_excel(
    start_s: int, channels: List[RidgelineChannel], sync_rows: List[RidgelineOutputRow]
) -> str:
    start_utc = pendulum.from_timestamp(start_s)
    start_local = start_utc.in_timezone(timezone_string)
    start_local.strftime("%Y/%m/%d %H:%M:%S")
    file_name = f"{OUT_STUB}/{start_local.strftime('%Y%m%d')}_freedom_flow.xlsx"
    print(f"Will attempt to write to {file_name}")
    workbook = xlsxwriter.Workbook(file_name)
    w_zoom = workbook.add_worksheet("zoom")
    w_min = workbook.add_worksheet("1-minute")
    w_min.freeze_panes(3, 0)
    header_format = workbook.add_format({"bg_color": "#E6F4D8", "align": "right"})
    data_format = workbook.add_format({"bg_color": "#E6F4D8"})
    date_width = 15
    channel_width = 11
    w_min.set_column("A:A", date_width)
    w_min.set_column("B:B", date_width)
    w_min.set_column("C:C", channel_width)
    w_min.set_column("D:D", channel_width)
    w_min.set_column("E:E", channel_width)
    w_min.set_column("F:F", channel_width)
    w_min.set_column("G:G", channel_width)
    w_min.set_column("H:H", 5)
    w_min.write(0, 0, "Start Date (ET)", header_format)
    w_min.write(1, 0, start_local.strftime("%Y/%m/%d"), header_format)
    w_min.write(0, 8, "csv.freedom.flow version 001")
    w_min.write(
        1, 8, "Data for Millinocket pilot first house (Freedom), from GridWorks"
    )

    w_min.write(2, 0, "Eastern Time", header_format)

    for i in range(len(channels)):
        ch = channels[i]
        w_min.write(0, 1 + i, ch.Channel.AboutName, header_format)
        w_min.write(1, 1 + i, ch.OutUnits.value, header_format)
        w_min.write(2, 1 + i, ch.DaveName, header_format)

    for i in range(len(sync_rows)):
        row = sync_rows[i]
        w_min.write(3 + i, 0, row.TimeEastern, data_format)
        w_min.write(3 + i, 1, row.DistSwtTempF, data_format)
        w_min.write(3 + i, 2, row.DistRwtTempF, data_format)
        w_min.write(3 + i, 3, row.DistFlowGpm, data_format)
        w_min.write(3 + i, 4, row.GlycolSwtTempF, data_format)
        w_min.write(3 + i, 5, row.GlycolRwtTempF, data_format)
        w_min.write(3 + i, 6, row.GlycolFlowGpm, data_format)

    w_zoom.set_column("A:A", date_width)
    w_zoom.set_column("B:B", channel_width)
    w_zoom.set_column("C:C", channel_width)
    w_zoom.set_column("D:D", channel_width)
    w_zoom.set_column("E:E", channel_width)
    w_zoom.set_column("F:F", channel_width)
    w_zoom.set_column("G:G", channel_width)
    w_zoom.set_column("H:H", 5)

    highlight_format = workbook.add_format({"bg_color": "yellow", "align": "right"})
    time_format = workbook.add_format({"num_format": "hh:mm:SS", "align": "right"})

    w_zoom.write(0, 0, "Start Time (HH:MM)")
    w_zoom.write(0, 1, "00:00", highlight_format)
    w_zoom.write(1, 0, "Duration (Hrs)")
    w_zoom.write(1, 1, "6", highlight_format)

    for i in range(len(channels)):
        ch = channels[i]
        w_zoom.write(3, 1 + i, ch.OutUnits.value, header_format)
        w_zoom.write(4, 1 + i, ch.DaveName, header_format)

    w_zoom.write("A6", "=B1", time_format)
    w_zoom.write("B6", "=OFFSET('1-minute'!B$4,$A6*24*60,0)")
    w_zoom.write("C6", "=OFFSET('1-minute'!C$4,$A6*24*60,0)")
    w_zoom.write("D6", "=OFFSET('1-minute'!D$4,$A6*24*60,0)")
    w_zoom.write("E6", "=OFFSET('1-minute'!E$4,$A6*24*60,0)")
    w_zoom.write("F6", "=OFFSET('1-minute'!F$4,$A6*24*60,0)")
    w_zoom.write("G6", "=OFFSET('1-minute'!G$4,$A6*24*60,0)")

    for i in range(1, len(sync_rows)):
        w_zoom.write(f"A{i + 6}", f"=A{i + 6 - 1} + $B$2/24/24/60", time_format)
        w_zoom.write(f"B{i + 6}", f"=OFFSET('1-minute'!B$4,$A{i + 6}*24*60,0)")
        w_zoom.write(f"C{i + 6}", f"=OFFSET('1-minute'!C$4,$A{i + 6}*24*60,0)")
        w_zoom.write(f"D{i + 6}", f"=OFFSET('1-minute'!D$4,$A{i + 6}*24*60,0)")
        w_zoom.write(f"E{i + 6}", f"=OFFSET('1-minute'!E$4,$A{i + 6}*24*60,0)")
        w_zoom.write(f"F{i + 6}", f"=OFFSET('1-minute'!F$4,$A{i + 6}*24*60,0)")
        w_zoom.write(f"G{i + 6}", f"=OFFSET('1-minute'!G$4,$A{i + 6}*24*60,0)")

    end = len(sync_rows) + 5
    dist_chart = workbook.add_chart({"type": "line"})
    dist_chart.add_series({
        "name": "zoom!$B$5",
        "categories": f"zoom!$A$6:$A${end}",
        "values": f"=zoom!$B$6:$B${end}",
        "line": {"color": "red"},
    })
    dist_chart.add_series({
        "name": "zoom!$C$5",
        "values": f"=zoom!$C$6:$C${end}",
        "line": {"color": "blue"},
    })
    dist_chart.add_series({
        "name": "zoom!$D$5",
        "values": f"=zoom!$D$6:$D${end}",
        "y2_axis": True,
        "line": {"color": "green"},
    })
    dist_flow_max = max(list(map(lambda x: x.DistFlowGpm, sync_rows)))
    dist_chart.set_y_axis({"name": "Deg F", "min": 90})
    dist_chart.set_y2_axis({"name": "Gpm", "max": 3 * dist_flow_max})
    dist_chart.set_title({
        "name": f'Distribution Loop {start_local.strftime("%m/%d/%Y")}'
    })
    dist_chart.set_size({"width": 720, "height": 432})
    w_zoom.insert_chart("I4", dist_chart)

    glycol_chart = workbook.add_chart({"type": "line"})
    glycol_chart.add_series({
        "name": "zoom!$E$5",
        "categories": f"zoom!$A$6:$A${end}",
        "values": f"=zoom!$E$6:$E${end}",
        "line": {"color": "red"},
    })
    glycol_chart.add_series({
        "name": "zoom!$F$5",
        "values": f"=zoom!$F$6:$F${end}",
        "line": {"color": "blue"},
    })
    glycol_chart.add_series({
        "name": "zoom!$G5",
        "values": f"=zoom!$G$6:$G${end}",
        "y2_axis": True,
        "line": {"color": "green"},
    })
    glycol_chart.set_y_axis({"name": "Deg F", "min": 90})
    glycol_chart.set_y2_axis({"name": "Gpm", "max": 24})
    glycol_chart.set_title({"name": f'Glycol Loop {start_local.strftime("%m/%d/%Y")}'})
    glycol_chart.set_size({"width": 720, "height": 432})
    w_zoom.insert_chart("I28", glycol_chart)

    workbook.close()
    return file_name


def make_spreadsheet(add_smoothing: bool = True) -> str:
    atn_alias = APPLE_ATN_ALIAS
    t = time.time()
    time_utc = pendulum.from_timestamp(t)

    last_utc_midnight_unix_s = t - (t % (3600 * 24))
    start_s = int(
        last_utc_midnight_unix_s
        + 3600 * (time_utc.hour - time_utc.in_timezone(timezone_string).hour)
    )
    start_time_unix_ms = int(start_s * 1000)
    duration_hrs = 24
    maker = ScadaReportA_Maker()
    rows = maker.get_readings(
        start_time_unix_ms=start_time_unix_ms,
        duration_hrs=duration_hrs,
        atn_alias=atn_alias,
    )

    temp_channels = [DIST_SWT, DIST_RWT, GLYCOL_SWT, GLYCOL_RWT]
    flow_channels = [DIST_FLOW, GLYCOL_FLOW]
    channels = [DIST_SWT, DIST_RWT, DIST_FLOW, GLYCOL_SWT, GLYCOL_RWT, GLYCOL_FLOW]

    readings = {}
    for ch in channels:
        readings[ch] = sorted(
            list(
                filter(
                    lambda x: x.Channel == ch.Channel,
                    rows,
                )
            ),
            key=lambda row: row.TimeUnixMs,
        )

    ridgeline_readings = {}
    for ch in flow_channels:
        dc_list = []
        for i in range(len(readings[ch])):
            flow_gpm = round(readings[ch][i].IntValue / 100, 1)
            dc_list.append(
                ChannelReading(
                    Channel=ch.Channel,
                    TimeUnixMs=readings[ch][i].TimeUnixMs,
                    FloatValue=flow_gpm,
                )
            )
        ridgeline_readings[ch] = dc_list

    for ch in temp_channels:
        dc_list = []
        for i in range(0, len(readings[ch])):
            temp_c = readings[ch][i].IntValue / 1000
            temp_f = round(c_to_f(temp_c), 2)
            dc_list.append(
                ChannelReading(
                    Channel=ch.Channel,
                    TimeUnixMs=readings[ch][i].TimeUnixMs,
                    FloatValue=temp_f,
                )
            )
        ridgeline_readings[ch] = dc_list

    sync_rows = []
    end_s = max(map(lambda x: x.TimeUnixMs, rows)) / 1000
    total_minutes = int((end_s - start_s) / 60)
    for i in range(total_minutes):
        sync_s = start_s + i * 60
        vals = {}
        for ch in channels:
            before = sorted(
                list(
                    filter(
                        lambda x: int(x.TimeUnixMs / 1000) <= sync_s,
                        ridgeline_readings[ch],
                    )
                ),
                key=lambda row: -row.TimeUnixMs,
            )
            if len(before) == 0:
                vals[ch] = None
            else:
                vals[ch] = before[0].FloatValue

        sync_rows.append(
            RidgelineOutputRow(
                TimeUtc=pendulum.from_timestamp(sync_s).strftime("%Y/%m/%d %H:%M:%S"),
                TimeEastern=pendulum.from_timestamp(sync_s)
                .in_timezone(timezone_string)
                .strftime("%H:%M"),
                DistSwtTempF=vals[DIST_SWT],
                DistRwtTempF=vals[DIST_RWT],
                DistFlowGpm=vals[DIST_FLOW],
                # DistFlowGpm=3.5,
                GlycolSwtTempF=vals[GLYCOL_SWT],
                GlycolRwtTempF=vals[GLYCOL_RWT],
                GlycolFlowGpm=vals[GLYCOL_FLOW],
                # GlycolFlowGpm=8.2
            )
        )
    return export_excel(start_s, channels, sync_rows)


# ch = DIST_FLOW
# #ch = GLYCOL_FLOW
# ch = DIST_RWT
# delta_s = []
# for i in range(1,len(readings[ch])):
#     row = readings[ch][i]
#     prev = readings[ch][i-1]
#     delta_s.append([row.TimeUtc, row.IntTimeUnixS, row.IntTimeUnixS - prev.IntTimeUnixS])
#
# med = list(filter(lambda x: x[2]>65, delta_s))
# print(delta_s)
#
# dist_flow_long =[['2023-03-28 00:33:50', 1679963630, 236],
#  ['2023-03-28 01:02:03', 1679965323, 124],
#  ['2023-03-28 01:09:36', 1679965776, 333],
#  ['2023-03-28 01:50:00', 1679968200, 302],
#  ['2023-03-28 04:22:04', 1679977324, 185],
#  ['2023-03-28 06:04:58', 1679983498, 315],
#  ['2023-03-28 06:13:21', 1679984001, 202],
#  ['2023-03-28 06:29:24', 1679984964, 297],
#  ['2023-03-28 07:47:58', 1679989678, 183],
#  ['2023-03-28 08:32:11', 1679992331, 180],
#  ['2023-03-28 10:51:45', 1680000705, 152],
#  ['2023-03-28 11:06:19', 1680001579, 86],
#  ['2023-03-28 13:18:53', 1680009533, 285]]
#
# glycol_flow_long = [['2023-03-28 00:33:50', 1679963630, 290],
#  ['2023-03-28 01:02:03', 1679965323, 179],
#  ['2023-03-28 01:09:36', 1679965776, 333],
#  ['2023-03-28 01:50:00', 1679968200, 302],
#  ['2023-03-28 04:22:04', 1679977324, 168],
#  ['2023-03-28 06:04:58', 1679983498, 307],
#  ['2023-03-28 06:13:21', 1679984001, 262],
#  ['2023-03-28 06:29:24', 1679984964, 297],
#  ['2023-03-28 07:47:58', 1679989678, 233],
#  ['2023-03-28 08:32:11', 1679992331, 178],
#  ['2023-03-28 10:51:45', 1680000705, 164],
#  ['2023-03-28 11:06:19', 1680001579, 89],
#  ['2023-03-28 13:18:53', 1680009533, 280]]
#
# dist_swt_above_65 = [['2023-03-28 00:33:47', 1679963627, 282],
#  ['2023-03-28 01:02:00', 1679965320, 124],
#  ['2023-03-28 01:09:33', 1679965773, 333],
#  ['2023-03-28 01:49:57', 1679968197, 318],
#  ['2023-03-28 04:22:01', 1679977321, 123],
#  ['2023-03-28 06:04:55', 1679983495, 335],
#  ['2023-03-28 06:13:18', 1679983998, 253],
#  ['2023-03-28 06:29:21', 1679984961, 275],
#  ['2023-03-28 07:47:55', 1679989675, 200],
#  ['2023-03-28 08:32:08', 1679992328, 177],
#  ['2023-03-28 10:51:42', 1680000702, 113],
#  ['2023-03-28 11:06:16', 1680001576, 78],
#  ['2023-03-28 13:18:50', 1680009530, 273]]
