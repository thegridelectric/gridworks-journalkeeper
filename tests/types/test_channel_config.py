"""Tests channel.config type, version 000"""

from gjk.enums import Unit
from gjk.named_types import ChannelConfig


def test_channel_config_generated() -> None:
    d = {
        "ChannelName": "hp-idu-pwr",
        "PollPeriodMs": 300,
        "CapturePeriodS": 60,
        "AsyncCapture": True,
        "AsyncCaptureDelta": 30,
        "Exponent": 6,
        "Unit": "Unknown",
        "TypeName": "channel.config",
        "Version": "000",
    }

    assert ChannelConfig.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, Unit="unknown_enum_thing")
    assert ChannelConfig.from_dict(d2).unit == Unit.default()
