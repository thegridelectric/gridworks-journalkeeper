"""Tests ticklist.reed.report type, version 000"""

from gjk.named_types import TicklistReedReport


def test_ticklist_reed_report_generated() -> None:
    d = {
        "TerminalAssetAlias": "d1.isone.ct.newhaven.orange1.ta",
        "ChannelName": "dist-flow",
        "ScadaReceivedUnixMs": 1730120522258,
        "Ticklist": {
            "HwUid": "pico_1fa376",
            "FirstTickTimestampNanoSecond": 1730120485296209000,
            "RelativeMillisecondList": [1730120513626],
            "PicoBeforePostTimestampNanoSecond": 1730120522058825000,
            "TypeName": "ticklist.reed",
            "Version": "101",
        },
        "TypeName": "ticklist.reed.report",
        "Version": "000",
    }

    assert TicklistReedReport.from_dict(d).to_dict() == d
