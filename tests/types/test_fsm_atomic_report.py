"""Tests fsm.atomic.report type, version 000"""

from gjk.enums import FsmActionType, FsmReportType
from gjk.named_types import FsmAtomicReport


def test_fsm_atomic_report_generated() -> None:
    d = {
        "MachineHandle": "h.picy-cycler.relay1",
        "StateEnum": "relay.closed.or.open",
        "ReportType": "Event",
        "EventEnum": "change.relay.state",
        "Event": "CloseRelay",
        "UnixTimeMs": 1709923792000,
        "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
        "TypeName": "fsm.atomic.report",
        "Version": "000",
    }

    assert FsmAtomicReport.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, ReportType="unknown_enum_thing")
    assert FsmAtomicReport.from_dict(d2).report_type == FsmReportType.default()

    d2 = dict(d, ActionType="unknown_enum_thing")
    assert FsmAtomicReport.from_dict(d2).action_type == FsmActionType.default()
