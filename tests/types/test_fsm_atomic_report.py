"""Tests fsm.atomic.report type, version 000"""

from gjk.named_types import FsmAtomicReport


def test_fsm_atomic_report_generated() -> None:
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

    d2 = FsmAtomicReport.from_dict(d).to_dict()

    assert d2 == d

    assert type(d2["AboutFsm"]) is str
