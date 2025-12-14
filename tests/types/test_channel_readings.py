"""Tests channel.readings type, version 002"""

from gjk.named_types import ChannelReadings


def test_channel_readings_generated() -> None:
    d = {
        "ChannelName": "hp-odu-pwr",
        "ValueList": [4559],
        "ScadaReadTimeUnixMsList": [1656443705023],
        "TypeName": "channel.readings",
        "Version": "002",
    }

    assert ChannelReadings.from_dict(d).to_dict() == d
