"""Tests channel.readings type, version 000"""

from gjk.types import ChannelReadings


def test_channel_readings_generated() -> None:
    t = ChannelReadings(
        channel_id="e601041c-8cb4-4e6f-9163-e6ad2edb1b72",
        value_list=[4559],
        scada_read_time_unix_ms_list=[1656443705023],
    )

    d = {
        "ChannelId": "e601041c-8cb4-4e6f-9163-e6ad2edb1b72",
        "ValueList": [4559],
        "ScadaReadTimeUnixMsList": [1656443705023],
        "TypeName": "channel.readings",
        "Version": "000",
    }

    assert t.to_dict() == d
    assert t == ChannelReadings.from_dict(d)
