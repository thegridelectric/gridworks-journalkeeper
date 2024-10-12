"""Tests keyparam.change.log type, version 000"""

from gjk.enums import KindOfParam
from gjk.named_types import KeyparamChangeLog


def test_keyparam_change_log_generated() -> None:
    d = {
        "AboutNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
        "ChangeTimeUtc": "2022-06-25T12:30:45.678",
        "Author": "Jessica Millar",
        "ParamName": "AdsMaxVoltage",
        "Description": "The maximum voltage used by thermistor temp sensing that rely on the ADS I2C chip. This transitions from being part of the code (pre) to part of the hardware layout (post)",
        "Kind": "Other",
        "TypeName": "keyparam.change.log",
        "Version": "000",
    }

    assert KeyparamChangeLog.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, Kind="unknown_enum_thing")
    assert KeyparamChangeLog.from_dict(d2).kind == KindOfParam.default()
