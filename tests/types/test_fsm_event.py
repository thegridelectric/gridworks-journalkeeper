"""Tests fsm.event type, version 000"""

from gjk.named_types import FsmEvent


def test_fsm_event_generated() -> None:
    d = {
        "FromHandle": "h.s.admin",
        "ToHandle": "h.s.admin.iso-valve",
        "EventType": "change.valve.state",
        "EventName": "OpenValve",
        "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
        "SendTimeUnixMs": 1709923791330,
        "TypeName": "fsm.event",
        "Version": "000",
    }

    t = FsmEvent.from_dict(d)
    assert t.to_dict() == d

