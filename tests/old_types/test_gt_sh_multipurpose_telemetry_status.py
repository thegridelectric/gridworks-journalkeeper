"""Tests gt.sh.multipurpose.telemetry.status type, version 100"""

from gjk.enums import TelemetryName
from gjk.old_types import GtShMultipurposeTelemetryStatus


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

    assert GtShMultipurposeTelemetryStatus.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, TelemetryName="unknown_enum_thing")
    assert (
        GtShMultipurposeTelemetryStatus.from_dict(d2).telemetry_name
        == TelemetryName.default()
    )
