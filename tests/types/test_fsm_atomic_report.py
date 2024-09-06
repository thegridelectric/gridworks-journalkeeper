"""Tests fsm.atomic.report, version 000"""

from gjk.enums import (
    FsmActionType,
    FsmEventType,
    FsmName,
    FsmReportType,
    RelayPinSet,
)
from gjk.types import FsmAtomicReport


def test_fsm_atomic_report_generated() -> None:
    t = FsmAtomicReport(
        from_handle="h.admin.store-charge-discharge.relay3",
        about_fsm=FsmName.RelayState,
        report_type=FsmReportType.Action,
        action_type=FsmActionType.RelayPinSet,
        action=RelayPinSet.DeEnergized.value,
        unix_time_ms=1710158001624,
        trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
    )

    d = {
        "FromHandle": "h.admin.store-charge-discharge.relay3",
        "AboutFsm": "RelayState",
        "ReportType": "Action",
        "ActionType": "RelayPinSet",
        "Action": 0,
        "UnixTimeMs": 1710158001624,
        "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
        "TypeName": "fsm.atomic.report",
        "Version": "000",
    }
    assert t.to_dict() == d
    assert t == FsmAtomicReport.from_dict(d)

    d2 = d.copy()
    del d2["AboutFsm"]
    d2["AboutFsmGtEnumSymbol"] = "1f560b73"
    del d2["ReportType"]
    d2["ReportTypeGtEnumSymbol"] = "490d4e1d"
    del d2["ActionType"]
    d2["ActionTypeGtEnumSymbol"] = "00000000"
    assert t == FsmAtomicReport.from_dict(d2)

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, AboutFsm="unknown_enum_thing")
    assert FsmAtomicReport.from_dict(d2).about_fsm == FsmName.default()

    d2 = dict(d, ReportType="unknown_enum_thing")
    assert FsmAtomicReport.from_dict(d2).report_type == FsmReportType.default()

    d2 = dict(d, ActionType="unknown_enum_thing")
    assert FsmAtomicReport.from_dict(d2).action_type == FsmActionType.default()

    d2 = dict(d, EventType="unknown_enum_thing")
    assert FsmAtomicReport.from_dict(d2).event_type == FsmEventType.default()
