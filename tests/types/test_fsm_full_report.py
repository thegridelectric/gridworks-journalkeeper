"""Tests fsm.full.report type, version 000"""

from gjk.enums import (
    ChangeRelayState,
    ChangeStoreFlowDirection,
    FsmActionType,
    FsmEventType,
    FsmName,
    FsmReportType,
    RelayClosedOrOpen,
    RelayPinSet,
    StoreFlowDirection,
)
from gjk.named_types import FsmAtomicReport, FsmFullReport


def test_fsm_full_report_generated() -> None:
    t = FsmFullReport(
        from_name="admin",
        trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
        atomic_list=[
            FsmAtomicReport(
                from_handle="h.admin.store-charge-discharge",
                about_fsm=FsmName.StoreFlowDirection,
                report_type=FsmReportType.Event,
                event_type=FsmEventType.ChangeStoreFlowDirection,
                event=ChangeStoreFlowDirection.Discharge.value,
                from_state=StoreFlowDirection.ValvedtoChargeStore.value,
                to_state=StoreFlowDirection.ValvesMovingToDischarging.value,
                unix_time_ms=1710158001595,
                trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
            ),
            FsmAtomicReport(
                from_handle="h.admin.store-charge-discharge.relay3",
                about_fsm=FsmName.RelayState,
                report_type=FsmReportType.Event,
                event_type=FsmEventType.ChangeRelayState,
                event=ChangeRelayState.OpenRelay.value,
                from_state=RelayClosedOrOpen.RelayClosed.value,
                to_state=RelayClosedOrOpen.RelayOpen.value,
                unix_time_ms=1710158001610,
                trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
            ),
            FsmAtomicReport(
                from_handle="h.admin.store-charge-discharge.relay3",
                about_fsm=FsmName.RelayState,
                report_type=FsmReportType.Action,
                action_type=FsmActionType.RelayPinSet,
                action=RelayPinSet.DeEnergized.value,
                unix_time_ms=1710158001624,
                trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
            ),
            FsmAtomicReport(
                from_handle="h.admin.store-charge-discharge",
                about_fsm=FsmName.StoreFlowDirection,
                report_type=FsmReportType.Event,
                event_type=FsmEventType.TimerFinished,
                event="Belimo BallValve232VS 45 second opening timer",
                from_state=StoreFlowDirection.ValvesMovingToDischarging.value,
                to_state=StoreFlowDirection.ValvedtoDischargeStore.value,
                unix_time_ms=1710158046849,
                trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
            ),
        ],
    )

    d = {
        "FromName": "admin",
        "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
        "AtomicList": [
            {
                "FromHandle": "h.admin.store-charge-discharge",
                "AboutFsm": "StoreFlowDirection",
                "ReportType": "Event",
                "EventType": "ChangeStoreFlowDirection",
                "Event": "Discharge",
                "FromState": "ValvedtoChargeStore",
                "ToState": "ValvesMovingToDischarging",
                "UnixTimeMs": 1710158001595,
                "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
                "TypeName": "fsm.atomic.report",
                "Version": "000",
            },
            {
                "FromHandle": "h.admin.store-charge-discharge.relay3",
                "AboutFsm": "RelayState",
                "ReportType": "Event",
                "EventType": "ChangeRelayState",
                "Event": "OpenRelay",
                "FromState": "RelayClosed",
                "ToState": "RelayOpen",
                "UnixTimeMs": 1710158001610,
                "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
                "TypeName": "fsm.atomic.report",
                "Version": "000",
            },
            {
                "FromHandle": "h.admin.store-charge-discharge.relay3",
                "AboutFsm": "RelayState",
                "ReportType": "Action",
                "ActionType": "RelayPinSet",
                "Action": 0,
                "UnixTimeMs": 1710158001624,
                "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
                "TypeName": "fsm.atomic.report",
                "Version": "000",
            },
            {
                "FromHandle": "h.admin.store-charge-discharge",
                "AboutFsm": "StoreFlowDirection",
                "ReportType": "Event",
                "EventType": "TimerFinished",
                "Event": "Belimo BallValve232VS 45 second opening timer",
                "FromState": "ValvesMovingToDischarging",
                "ToState": "ValvedtoDischargeStore",
                "UnixTimeMs": 1710158046849,
                "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
                "TypeName": "fsm.atomic.report",
                "Version": "000",
            },
        ],
        "TypeName": "fsm.full.report",
        "Version": "000",
    }

    assert t.to_dict() == d
    assert t == FsmFullReport.from_dict(d)
