"""Tests fsm.full.report type, version 000"""

from gjk.enums import (
    ChangeRelayState,
    ChangeStoreFlowRelay,
    FsmReportType,
    RelayClosedOrOpen,
    StoreFlowRelay,
)
from gjk.named_types import FsmAtomicReport, FsmFullReport


def test_fsm_full_report_generated() -> None:
    t = FsmFullReport(
        from_name="admin",
        trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
        atomic_list=[
            FsmAtomicReport(
                machine_handle="h.admin.store-charge-discharge",
                state_enum=StoreFlowRelay.enum_name(),
                report_type=FsmReportType.Event,
                event_enum=ChangeStoreFlowRelay.enum_name(),
                event=ChangeStoreFlowRelay.ChargeStore,
                from_state=StoreFlowRelay.DischargingStore,
                to_state=StoreFlowRelay.ChargingStore,
                unix_time_ms=1710158001595,
                trigger_id="12da4269-63c3-44f4-ab65-3ee5e29329fe",
            ),
            FsmAtomicReport(
                machine_handle="h.admin.store-charge-discharge.relay3",
                state_enum=RelayClosedOrOpen.enum_name(),
                report_type=FsmReportType.Event,
                event_enum=ChangeRelayState.enum_name(),
                event=ChangeRelayState.OpenRelay,
                from_state=RelayClosedOrOpen.RelayClosed,
                to_state=RelayClosedOrOpen.RelayOpen,
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
                "MachineHandle": "h.admin.store-charge-discharge",
                "StateEnum": "store.flow.relay",
                "ReportType": "Event",
                "EventEnum": "change.store.flow.relay",
                "Event": "ChargeStore",
                "FromState": "DischargingStore",
                "ToState": "ChargingStore",
                "UnixTimeMs": 1710158001595,
                "TriggerId": "12da4269-63c3-44f4-ab65-3ee5e29329fe",
            },
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
            },
        ],
    }

    assert t.to_dict() == d
    assert t == FsmFullReport.from_dict(d)
