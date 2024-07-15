"""
Tests for enum fsm.report.type.000 from the GridWorks Type Registry.
"""

from gwp.enums import FsmReportType


def test_fsm_report_type() -> None:
    assert set(FsmReportType.values()) == {
        "Other",
        "Event",
        "Action",
    }

    assert FsmReportType.default() == FsmReportType.Other
    assert FsmReportType.enum_name() == "fsm.report.type"
    assert FsmReportType.enum_version() == "000"

    assert FsmReportType.version("Other") == "000"
    assert FsmReportType.version("Event") == "000"
    assert FsmReportType.version("Action") == "000"

    for value in FsmReportType.values():
        symbol = FsmReportType.value_to_symbol(value)
        assert FsmReportType.symbol_to_value(symbol) == value
