"""Tests gridworks.event.gt.sh.status type, version 000"""

import json

import pytest
from gw.errors import GwTypeError
from pydantic import ValidationError

from gjk.types import GridworksEventGtShStatus
from gjk.types import GridworksEventGtShStatus_Maker as Maker


def test_gridworks_event_gt_sh_status_generated() -> None:
    t = GridworksEventGtShStatus(
        message_id='2952731d-a415-44de-b37c-f5f865dee77b',
        time_n_s=1699886100019488593,
        src='hw1.isone.me.versant.keene.beech.scada',
        status={ "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada", "FromGNodeId": "b98eadcf-aeff-4ef6-96f0-c8641bae6909", "AboutGNodeAlias": "dummy.ta", "SlotStartUnixS": 1699885800, "ReportingPeriodS": 300, "SimpleTelemetryList": [ { "ShNodeAlias": "a.dist.flow", "TelemetryName": "GallonsTimes100", "ValueList": [ 478060, 478060, 478060, 478060, 478060, 478060, 478060, 478060, 478060 ], "ReadTimeUnixMsList": [ 1699885826322, 1699885856324, 1699885886323, 1699885916871, 1699885948047, 1699885978862, 1699886008715, 1699886039477, 1699886069538 ], "TypeName": "gt.sh.simple.telemetry.status", "Version": "100" } ], "MultipurposeTelemetryList": [ { "AboutNodeAlias": "a.hp.fossil.lwt.temp", "SensorNodeAlias": "a.s.analog.temp", "TelemetryName": "WaterTempCTimes1000", "ValueList": [ -42027, -37525, -36790, -37600, -37581 ], "ReadTimeUnixMsList": [ 1699885810070, 1699885870269, 1699885930078, 1699885990620, 1699886050455 ], "TypeName": "gt.sh.multipurpose.telemetry.status", "Version": "100" }, ], "BooleanactuatorCmdList": [], "StatusUid": "55faec9b-7ce6-4a64-9d5d-e07e20cf6e15", "TypeName": "gt.sh.status", "Version": "110" },
    )

    d = {
        "MessageId": '2952731d-a415-44de-b37c-f5f865dee77b',
        "TimeNS": 1699886100019488593,
        "Src": 'hw1.isone.me.versant.keene.beech.scada',
        "Status": { "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada", "FromGNodeId": "b98eadcf-aeff-4ef6-96f0-c8641bae6909", "AboutGNodeAlias": "dummy.ta", "SlotStartUnixS": 1699885800, "ReportingPeriodS": 300, "SimpleTelemetryList": [ { "ShNodeAlias": "a.dist.flow", "TelemetryName": "GallonsTimes100", "ValueList": [ 478060, 478060, 478060, 478060, 478060, 478060, 478060, 478060, 478060 ], "ReadTimeUnixMsList": [ 1699885826322, 1699885856324, 1699885886323, 1699885916871, 1699885948047, 1699885978862, 1699886008715, 1699886039477, 1699886069538 ], "TypeName": "gt.sh.simple.telemetry.status", "Version": "100" } ], "MultipurposeTelemetryList": [ { "AboutNodeAlias": "a.hp.fossil.lwt.temp", "SensorNodeAlias": "a.s.analog.temp", "TelemetryName": "WaterTempCTimes1000", "ValueList": [ -42027, -37525, -36790, -37600, -37581 ], "ReadTimeUnixMsList": [ 1699885810070, 1699885870269, 1699885930078, 1699885990620, 1699886050455 ], "TypeName": "gt.sh.multipurpose.telemetry.status", "Version": "100" }, ], "BooleanactuatorCmdList": [], "StatusUid": "55faec9b-7ce6-4a64-9d5d-e07e20cf6e15", "TypeName": "gt.sh.status", "Version": "110" },
        "TypeName": "gridworks.event.gt.sh.status",
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
    del d2["MessageId"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TimeNS"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Src"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Status"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, TimeNS="1699886100019488593.1")
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

    d2 = dict(d, MessageId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, Src="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
