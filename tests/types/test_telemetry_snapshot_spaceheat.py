"""Tests telemetry.snapshot.spaceheat type, version 000"""

from gjk.types import TelemetrySnapshotSpaceheat


def test_telemetry_snapshot_spaceheat_generated() -> None:
    d = {
        "ReportTimeUnixMs": 1656363448000,
        "AboutNodeAliasList": ["a.elt1.relay", "a.tank.temp0"],
        "ValueList": [1, 66086],
        "TelemetryNameList": ["RelayState", "WaterTempCTimes1000"],
        "TypeName": "telemetry.snapshot.spaceheat",
        "Version": "000",
    }

    t = TelemetrySnapshotSpaceheat.from_dict(d)
    assert t.to_dict() == d

    d2 = d.copy()
    d2["TelemetryNameList"] = ["5a71d4b3", "c89d0ba1"]
    assert t == TelemetrySnapshotSpaceheat.from_dict(d2)
