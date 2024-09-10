"""Tests batched.readings type, version 000"""

from gjk.types import BatchedReadings


def test_batched_readings_generated() -> None:
    d = {
        "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
        "FromGNodeInstanceId": "98542a17-3180-4f2a-a929-6023f0e7a106",
        "AboutGNodeAlias": "hw1.isone.me.versant.keene.beech.ta",
        "SlotStartUnixS": 1708518780,
        "BatchedTransmissionPeriodS": 30,
        "MessageCreatedMs": 1708518810017,
        "DataChannelList": [
            {
                "Name": "hp-odu-pwr",
                "DisplayName": "HP ODU Power",
                "AboutNodeName": "hp-odu",
                "CapturedByNodeName": "primary-pwr-meter",
                "TelemetryName": "PowerW",
                "TerminalAssetAlias": "hw1.isone.me.versant.keene.beech.ta",
                "InPowerMetering": True,
                "StartS": 1704862800,
                "Id": "498da855-bac5-47e9-b83a-a11e56a50e67",
                "TypeName": "data.channel.gt",
                "Version": "001",
            },
            {
                "Name": "hp-idu-pwr",
                "DisplayName": "HP IDU Power",
                "AboutNodeName": "hp-idu",
                "CapturedByNodeName": "primary-pwr-meter",
                "TelemetryName": "PowerW",
                "TerminalAssetAlias": "hw1.isone.me.versant.keene.beech.ta",
                "InPowerMetering": True,
                "StartS": 1704862800,
                "Id": "beabac86-7caa-4ab4-a50b-af1ad54ed165",
                "TypeName": "data.channel.gt",
                "Version": "001",
            },
        ],
        "ChannelReadingList": [
            {
                "ChannelId": "498da855-bac5-47e9-b83a-a11e56a50e67",
                "ValueList": [26, 96, 196],
                "ScadaReadTimeUnixMsList": [
                    1708518800235,
                    1708518808236,
                    1708518809232,
                ],
                "TypeName": "channel.readings",
                "Version": "000",
            },
            {
                "ChannelId": "beabac86-7caa-4ab4-a50b-af1ad54ed165",
                "ValueList": [14],
                "ScadaReadTimeUnixMsList": [1708518800235],
                "TypeName": "channel.readings",
                "Version": "000",
            },
        ],
        "FsmActionList": [],
        "FsmReportList": [],
        "Id": "4dab57dd-8b4e-4ea4-90a3-d63df9eeb061",
        "TypeName": "batched.readings",
        "Version": "000",
    }

    t = BatchedReadings.from_dict(d)
    assert t.to_dict() == d
