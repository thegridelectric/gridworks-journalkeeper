"""Tests my.channels.event type, version 000"""

from gjk.named_types import MyChannelsEvent


def test_my_channels_event_generated() -> None:
    d = {
        "MessageId": "1302c0f8-1983-43b2-90d2-61678d731db3",
        "TimeCreatedMs": 1728651445746,
        "Src": "hw1.isone.me.versant.keene.beech.scada",
        "MyChannels": {
            "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
            "FromGNodeInstanceId": "98542a17-3180-4f2a-a929-6023f0e7a106",
            "MessageCreatedMs": 1728651445746,
            "MessageId": "1302c0f8-1983-43b2-90d2-61678d731db3",
            "ChannelList": [
                {
                    "Name": "hp-idu-pwr",
                    "DisplayName": "Hp IDU",
                    "AboutNodeName": "hp-idu-pwr",
                    "CapturedByNodeName": "power-meter",
                    "TelemetryName": "PowerW",
                    "TerminalAssetAlias": "hw1.isone.me.versant.keene.beech.ta",
                    "InPowerMetering": True,
                    "StartS": 1721405699,
                    "Id": "50cf426b-ff3f-4a30-8415-8d3fba5e0ab7",
                    "TypeName": "data.channel.gt",
                    "Version": "001",
                }
            ],
            "TypeName": "my.channels",
            "Version": "000",
        },
        "TypeName": "my.channels.event",
        "Version": "000",
    }

    assert MyChannelsEvent.from_dict(d).to_dict() == d
