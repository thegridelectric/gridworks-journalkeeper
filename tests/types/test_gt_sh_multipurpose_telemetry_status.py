"""Tests gt.sh.multipurpose.telemetry.status type, version 100"""

from gjk.enums import TelemetryName
from gjk.types import GtShMultipurposeTelemetryStatus


def test_gt_sh_multipurpose_telemetry_status_generated() -> None:
    d = {
        "AboutNodeAlias": "a.elt1",
        "SensorNodeAlias": "a.m",
        "TelemetryName": "PowerW",
        "ValueList": [4559],
        "ReadTimeUnixMsList": [1656443705023],
        "TypeName": "gt.sh.multipurpose.telemetry.status",
        "Version": "100",
    }

    t = GtShMultipurposeTelemetryStatus.from_dict(d)
    assert t.to_dict() == d

    d2 = d.copy()
    del d2["TelemetryName"]
    d2["TelemetryNameGtEnumSymbol"] = "af39eec9"
    assert t == GtShMultipurposeTelemetryStatus.from_dict(d2)

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, TelemetryName="unknown_enum_thing")
    assert (
        GtShMultipurposeTelemetryStatus.from_dict(d2).telemetry_name
        == TelemetryName.default()
    )
