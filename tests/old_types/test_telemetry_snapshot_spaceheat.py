"""Tests telemetry.snapshot.spaceheat type, version 000"""

from gjk.old_types import TelemetrySnapshotSpaceheat


def test_telemetry_snapshot_spaceheat_generated() -> None:
    d = {
        "ReportTimeUnixMs": 1656363448000,
        "AboutNodeAliasList": ["a.elt1.relay", "a.tank.temp0"],
        "ValueList": [1, 66086],
        "TelemetryNameList": ["5a71d4b3", "c89d0ba1"],
        "TypeName": "telemetry.snapshot.spaceheat",
        "Version": "000",
    }

    assert TelemetrySnapshotSpaceheat.from_dict(d).to_dict() == d
