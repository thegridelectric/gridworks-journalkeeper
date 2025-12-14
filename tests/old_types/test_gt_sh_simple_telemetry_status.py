"""Tests gt.sh.simple.telemetry.status type, version 100"""

from gjk.enums import TelemetryName
from gjk.old_types import GtShSimpleTelemetryStatus


def test_gt_sh_simple_telemetry_status_generated() -> None:
    d = {
        "ShNodeAlias": "a.elt1.relay",
        "TelemetryName": "RelayState",
        "ValueList": [0],
        "ReadTimeUnixMsList": [1656443705023],
        "TypeName": "gt.sh.simple.telemetry.status",
        "Version": "100",
    }

    t = GtShSimpleTelemetryStatus.from_dict(d)
    assert t.to_dict() == d

    d2 = d.copy()
    del d2["TelemetryName"]
    d2["TelemetryNameGtEnumSymbol"] = "5a71d4b3"
    assert t == GtShSimpleTelemetryStatus.from_dict(d2)

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, TelemetryName="unknown_enum_thing")
    assert (
        GtShSimpleTelemetryStatus.from_dict(d2).telemetry_name
        == TelemetryName.default()
    )
