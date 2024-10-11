"""Tests snapshot.spaceheat type, version 001"""

from gjk.named_types import SnapshotSpaceheat


def test_snapshot_spaceheat_generated() -> None:
    d = {
        "FromGNodeAlias": "d1.isone.ct.newhaven.rose.scada",
        "FromGNodeInstanceId": "0384ef21-648b-4455-b917-58a1172d7fc1",
        "SnapshotTimeUnixMs": 1709915800472,
        "LatestReadingList": [],
        "TypeName": "snapshot.spaceheat",
        "Version": "001",
    }

    assert SnapshotSpaceheat.from_dict(d).to_dict() == d
