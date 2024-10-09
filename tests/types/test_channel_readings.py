"""Tests channel.readings type, version 001"""

from gjk.types import ChannelReadings


def test_channel_readings_generated() -> None:
    d = {
        "ChannelName": "hp-odu-pwr",
        "ChannelId": "498da855-bac5-47e9-b83a-a11e56a50e67",
        "ValueList": [4559],
        "ScadaReadTimeUnixMsList": [1656443705023],
        "TypeName": "channel.readings",
        "Version": "001",
    }

    t = ChannelReadings.from_dict(d)
    assert t.to_dict() == d
