"""Tests snapshot.spaceheat type, version 000"""

from gjk.types import SnapshotSpaceheat


def test_snapshot_spaceheat_generated() -> None:
    d = {
        "FromGNodeAlias": "dwtest.isone.ct.newhaven.orange1.ta.scada",
        "FromGNodeInstanceId": "0384ef21-648b-4455-b917-58a1172d7fc1",
        "Snapshot": {
            "TelemetryNameList": ["RelayState"],
            "AboutNodeAliasList": ["a.elt1.relay"],
            "ReportTimeUnixMs": 1656363448000,
            "ValueList": [1],
            "TypeName": "telemetry.snapshot.spaceheat",
            "Version": "000",
        },
        "TypeName": "snapshot.spaceheat",
        "Version": "000",
    }

    t = SnapshotSpaceheat.from_dict(d)
    assert t.to_dict() == d
