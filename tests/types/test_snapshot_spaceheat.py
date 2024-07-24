"""Tests snapshot.spaceheat type, version 000"""

import json

import pytest
from gw.errors import GwTypeError
from pydantic import ValidationError

from gjk.types import SnapshotSpaceheat
from gjk.types import SnapshotSpaceheat_Maker as Maker


def test_snapshot_spaceheat_generated() -> None:
    t = SnapshotSpaceheat(
        from_g_node_alias="dwtest.isone.ct.newhaven.orange1.ta.scada",
        from_g_node_instance_id="0384ef21-648b-4455-b917-58a1172d7fc1",
        snapshot={"TelemetryNameList": ["5a71d4b3"], "AboutNodeAliasList": ["a.elt1.relay"], "ReportTimeUnixMs": 1656363448000, "ValueList": [1], "TypeName": "telemetry.snapshot.spaceheat", "Version": "000"},
    )

    d = {
        "FromGNodeAlias": "dwtest.isone.ct.newhaven.orange1.ta.scada",
        "FromGNodeInstanceId": "0384ef21-648b-4455-b917-58a1172d7fc1",
        "Snapshot": {"TelemetryNameList": ["5a71d4b3"], "AboutNodeAliasList": ["a.elt1.relay"], "ReportTimeUnixMs": 1656363448000, "ValueList": [1], "TypeName": "telemetry.snapshot.spaceheat", "Version": "000"},
        "TypeName": "snapshot.spaceheat",
        "Version": "000",
    }

    assert t.as_dict() == d

    with pytest.raises(GwTypeError):
        Maker.type_to_tuple(d)

    with pytest.raises(GwTypeError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gtype = json.dumps(d)
    gtuple = Maker.type_to_tuple(gtype)
    assert gtuple == t

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gtuple)) == gtuple

    ######################################
    # GwTypeError raised if missing a required attribute
    ######################################

    d2 = dict(d)
    del d2["TypeName"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["FromGNodeAlias"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["FromGNodeInstanceId"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Snapshot"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    ######################################
    # ValidationError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type name")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # ValidationError raised if primitive attributes do not have appropriate property_format
    ######################################

    d2 = dict(d, FromGNodeAlias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FromGNodeInstanceId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
