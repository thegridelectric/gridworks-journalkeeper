"""Tests report type, version 000"""

from gjk.types import Report


def test_report_generated() -> None:
    d = {
        "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
        "FromGNodeInstanceId": "98542a17-3180-4f2a-a929-6023f0e7a106",
        "AboutGNodeAlias": "hw1.isone.me.versant.keene.beech.ta",
        "SlotStartUnixS": 1708518780,
        "BatchedTransmissionPeriodS": 30,
        "MessageCreatedMs": 1708518810017,
        "ChannelReadingList": [
            {
                "ChannelName": "hp-odu-pwr",
                "ChannelId": "498da855-bac5-47e9-b83a-a11e56a50e67",
                "ValueList": [26, 96, 196],
                "ScadaReadTimeUnixMsList": [
                    1708518800235,
                    1708518808236,
                    1708518809232,
                ],
                "TypeName": "channel.readings",
                "Version": "001",
            },
            {
                "ChannelName": "dist-pump-pwr",
                "ChannelId": "a2ebe9fa-05ba-4665-a6ba-dbc85aee530c",
                "ValueList": [14],
                "ScadaReadTimeUnixMsList": [1708518800235],
                "TypeName": "channel.readings",
                "Version": "001",
            },
        ],
        "FsmActionList": [],
        "FsmReportList": [],
        "Id": "4dab57dd-8b4e-4ea4-90a3-d63df9eeb061",
        "TypeName": "report",
        "Version": "000",
    }

    d2 = Report.from_dict(d).to_dict()
    assert d2 == d
