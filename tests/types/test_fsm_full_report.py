"""Tests fsm.full.report type, version 000"""

from gjk.enums import (
    ChangeRelayState,
    FsmReportType,
    RelayClosedOrOpen,
)
from gjk.named_types import FsmAtomicReport, FsmFullReport


def test_fsm_full_report_generated() -> None:
    t = FsmFullReport(
        from_name="admin",
        trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
        atomic_list=[
            FsmAtomicReport(
                machine_handle="h.admin.store-charge-discharge.relay3",
                state_enum="relay.closed.or.open",
                report_type=FsmReportType.Event,
                event_enum=ChangeRelayState.enum_name(),
                event=ChangeRelayState.OpenRelay.value,
                from_state=RelayClosedOrOpen.RelayClosed.value,
                to_state=RelayClosedOrOpen.RelayOpen.value,
                unix_time_ms=1710158001610,
                trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
            ),
        ],
    )

    d = {
        "TypeName": "fsm.full.report",
        "Version": "000",
        "FromName": "admin",
        "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
        "AtomicList": [
            {
                "TypeName": "fsm.atomic.report",
                "Version": "000",
                "MachineHandle": "h.admin.store-charge-discharge.relay3",
                "StateEnum": "relay.closed.or.open",
                "ReportType": "Event",
                "EventEnum": "change.relay.state",
                "Event": "OpenRelay",
                "FromState": "RelayClosed",
                "ToState": "RelayOpen",
                "UnixTimeMs": 1710158001610,
                "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
            }
        ],
    }

    assert t.to_dict() == d
    assert t == FsmFullReport.from_dict(d)
