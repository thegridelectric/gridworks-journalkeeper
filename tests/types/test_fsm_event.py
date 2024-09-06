"""Tests fsm.event type, version 000"""

from gjk.enums import FsmEventType
from gjk.types import FsmEvent


def test_fsm_event_generated() -> None:

    d = {
        "FromHandle": "h.s.admin",
        "ToHandle": "h.s.admin.iso-valve",
        "EventType": "ChangeValveState",
        "EventName": "OpenValve",
        "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
        "SendTimeUnixMs": 1709923791330,
        "TypeName": "fsm.event",
        "Version": "000",
    }

    t = FsmEvent.from_dict(d)
    assert t.to_dict() == d

    d2 = d.copy()
    del d2["EventType"]
    d2["EventTypeGtEnumSymbol"] = "c234ee7a"
    assert t == FsmEvent.from_dict(d2)

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, EventType="unknown_enum_thing")
    assert FsmEvent.from_dict(d2).event_type == FsmEventType.default()
