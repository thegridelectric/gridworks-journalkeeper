"""Tests gt.sh.simple.telemetry.status type, version 100"""

import json

import pytest
from gw.errors import GwTypeError
from pydantic import ValidationError

from gjk.enums import TelemetryName
from gjk.types import GtShSimpleTelemetryStatus
from gjk.types import GtShSimpleTelemetryStatus_Maker as Maker


def test_gt_sh_simple_telemetry_status_generated() -> None:
    t = GtShSimpleTelemetryStatus(
        sh_node_alias="a.elt1.relay",
        telemetry_name="5a71d4b3",
        value_list=[0],
        read_time_unix_ms_list=[1656443705023],
    )

    d = {
        "ShNodeAlias": "a.elt1.relay",
        "TelemetryNameGtEnumSymbol": "5a71d4b3",
        "ValueList": [0],
        "ReadTimeUnixMsList": [1656443705023],
        "TypeName": "gt.sh.simple.telemetry.status",
        "Version": "100",
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
    del d2["ShNodeAlias"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TelemetryNameGtEnumSymbol"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ValueList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ReadTimeUnixMsList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, TelemetryNameGtEnumSymbol="unknown_symbol")
    Maker.dict_to_tuple(d2).telemetry_name == TelemetryName.default()

    ######################################
    # ValidationError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type name")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # ValidationError raised if primitive attributes do not have appropriate property_format
    ######################################

    d2 = dict(d, ShNodeAlias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ReadTimeUnixMsList=[1656245000])
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
