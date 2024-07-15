"""Tests gt.sh.status type, version 110"""

import json

import pytest
from gw.errors import GwTypeError
from pydantic import ValidationError

from gwp.types import GtShStatus
from gwp.types import GtShStatus_Maker as Maker


def test_gt_sh_status_generated() -> None:
    t = GtShStatus(
        from_g_node_alias="dwtest.isone.ct.newhaven.orange1.ta.scada",
        from_g_node_id="0384ef21-648b-4455-b917-58a1172d7fc1",
        about_g_node_alias="dwtest.isone.ct.newhaven.orange1.ta",
        slot_start_unix_s=1656945300,
        reporting_period_s=300,
        simple_telemetry_list=[ { "ValueList": [0, 1], "ReadTimeUnixMsList": [1656945400527, 1656945414270], "ShNodeAlias": "a.elt1.relay", "TypeName": "gt.sh.simple.telemetry.status", "Version": "100", "TelemetryNameGtEnumSymbol": "5a71d4b3", } ],
        multipurpose_telemetry_list=[ { "AboutNodeAlias": "a.elt1", "ValueList": [18000], "ReadTimeUnixMsList": [1656945390152], "SensorNodeAlias": "a.m", "TypeName": "gt.sh.multipurpose.telemetry.status", "Version": "100", "TelemetryNameGtEnumSymbol": "ad19e79c", } ],
        booleanactuator_cmd_list=[ { "ShNodeAlias": "a.elt1.relay", "RelayStateCommandList": [1], "CommandTimeUnixMsList": [1656945413464], "TypeName": "gt.sh.booleanactuator.cmd.status", "Version": "100", } ],
        status_uid="dedc25c2-8276-4b25-abd6-f53edc79b62b",
    )

    d = {
        "FromGNodeAlias": "dwtest.isone.ct.newhaven.orange1.ta.scada",
        "FromGNodeId": "0384ef21-648b-4455-b917-58a1172d7fc1",
        "AboutGNodeAlias": "dwtest.isone.ct.newhaven.orange1.ta",
        "SlotStartUnixS": 1656945300,
        "ReportingPeriodS": 300,
        "SimpleTelemetryList": [ { "ValueList": [0, 1], "ReadTimeUnixMsList": [1656945400527, 1656945414270], "ShNodeAlias": "a.elt1.relay", "TypeName": "gt.sh.simple.telemetry.status", "Version": "100", "TelemetryNameGtEnumSymbol": "5a71d4b3", } ],
        "MultipurposeTelemetryList": [ { "AboutNodeAlias": "a.elt1", "ValueList": [18000], "ReadTimeUnixMsList": [1656945390152], "SensorNodeAlias": "a.m", "TypeName": "gt.sh.multipurpose.telemetry.status", "Version": "100", "TelemetryNameGtEnumSymbol": "ad19e79c", } ],
        "BooleanactuatorCmdList": [ { "ShNodeAlias": "a.elt1.relay", "RelayStateCommandList": [1], "CommandTimeUnixMsList": [1656945413464], "TypeName": "gt.sh.booleanactuator.cmd.status", "Version": "100", } ],
        "StatusUid": "dedc25c2-8276-4b25-abd6-f53edc79b62b",
        "TypeName": "gt.sh.status",
        "Version": "110",
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
    del d2["FromGNodeId"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["AboutGNodeAlias"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["SlotStartUnixS"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ReportingPeriodS"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["SimpleTelemetryList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["MultipurposeTelemetryList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["BooleanactuatorCmdList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["StatusUid"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, SlotStartUnixS="1656945300.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ReportingPeriodS="300.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, SimpleTelemetryList="Not a list.")
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, SimpleTelemetryList=["Not a list of dicts"])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, SimpleTelemetryList= [{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, MultipurposeTelemetryList="Not a list.")
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, MultipurposeTelemetryList=["Not a list of dicts"])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, MultipurposeTelemetryList= [{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, BooleanactuatorCmdList="Not a list.")
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, BooleanactuatorCmdList=["Not a list of dicts"])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, BooleanactuatorCmdList= [{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(GwTypeError):
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

    d2 = dict(d, FromGNodeAlias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FromGNodeId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, AboutGNodeAlias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, SlotStartUnixS=32503683600)
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, StatusUid="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
