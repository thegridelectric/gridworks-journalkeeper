"""Tests gridworks.event.snapshot.spaceheat type, version 000"""

from gjk.old_types import GridworksEventSnapshotSpaceheat


def test_gridworks_event_snapshot_spaceheat_generated() -> None:
    d = {
        "MessageId": "5f69d6d6-7da2-4f2a-ac06-6a298ee2fa70",
        "TimeNS": 1699886100019488593,
        "Src": "hw1.isone.me.versant.keene.beech.scada",
        "Snap": {
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
        },
        "TypeName": "gridworks.event.snapshot.spaceheat",
        "Version": "000",
    }

    t = GridworksEventSnapshotSpaceheat.from_dict(d)
    assert t.to_dict() == d
