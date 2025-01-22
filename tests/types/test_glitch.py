"""Tests glitch type, version 000"""

from gjk.enums import LogLevel
from gjk.named_types import Glitch


def test_glitch_generated() -> None:
    d = {
        "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
        "Node": "power-meter",
        "Type": "Warning",
        "Summary": "Driver problems: read warnings for (EGAUGE__4030)",
        "Details": "Problems: 0 errors, 2 warnings, max: 10",
        "CreatedMs": 1736825676763,
        "TypeName": "glitch",
        "Version": "000",
    }

    assert Glitch.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, Type="unknown_enum_thing")
    assert Glitch.from_dict(d2).type == LogLevel.default()
