"""Tests telemetry.snapshot.spaceheat type, version 000"""

import json

import pytest
from gw.errors import GwTypeError
from pydantic import ValidationError

from gjk.enums import TelemetryName
from gjk.types import TelemetrySnapshotSpaceheat
from gjk.types import TelemetrySnapshotSpaceheat_Maker as Maker


def test_telemetry_snapshot_spaceheat_generated() -> None:
    t = TelemetrySnapshotSpaceheat(
        report_time_unix_ms=1656363448000,
        about_node_alias_list=["a.elt1.relay", "a.tank.temp0"],
        value_list=[1, 66086],
        telemetry_name_list=["5a71d4b3", "c89d0ba1"],
    )

    d = {
        "ReportTimeUnixMs": 1656363448000,
        "AboutNodeAliasList": ["a.elt1.relay", "a.tank.temp0"],
        "ValueList": [1, 66086],
        "TelemetryNameList": ["5a71d4b3", "c89d0ba1"],
        "TypeName": "telemetry.snapshot.spaceheat",
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
    del d2["ReportTimeUnixMs"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["AboutNodeAliasList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ValueList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TelemetryNameList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, ReportTimeUnixMs="1656363448000.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # ValidationError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type name")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # ValidationError raised if primitive attributes do not have appropriate property_format
    ######################################

    d2 = dict(d, ReportTimeUnixMs=1656245000)
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, AboutNodeAliasList=["a.b-h"])
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
