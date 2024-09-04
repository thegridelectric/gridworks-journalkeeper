"""Tests fsm.event type, version 000"""

import json

import pytest
from gw.errors import GwTypeError
from gjk.enums import FsmEventType
from gjk.types import FsmEvent
from gjk.types import FsmEventMaker as Maker
from pydantic import ValidationError


def test_fsm_event_generated() -> None:
    t = FsmEvent(
        from_handle="h.s.admin",
        to_handle="h.s.admin.iso-valve",
        event_type=FsmEventType.ChangeValveState,
        event_name="OpenValve",
        trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
        send_time_unix_ms=1709923791330,
    )

    d = {
        "FromHandle": "h.s.admin",
        "ToHandle": "h.s.admin.iso-valve",
        "EventTypeGtEnumSymbol": "c234ee7a",
        "EventName": "OpenValve",
        "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
        "SendTimeUnixMs": 1709923791330,
        "TypeName": "fsm.event",
        "Version": "000",
    }

    assert t.as_dict() == d

    d2 = d.copy()

    del d2["EventTypeGtEnumSymbol"]
    d2["EventType"] = FsmEventType.ChangeValveState.value
    assert t == Maker.dict_to_tuple(d2)

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

    d2 = d.copy()
    del d2["TypeName"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["FromHandle"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["ToHandle"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["EventTypeGtEnumSymbol"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["EventName"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["TriggerId"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["SendTimeUnixMs"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, EventTypeGtEnumSymbol="unknown_symbol", EventName="CloseRelay")
    assert Maker.dict_to_tuple(d2).event_type == FsmEventType.default()

    d2 = dict(d, SendTimeUnixMs="1709923791330.1")
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

    d2 = dict(d, FromHandle="A.hot-stuff")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ToHandle="A.hot-stuff")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, TriggerId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, SendTimeUnixMs=1656245000)
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
