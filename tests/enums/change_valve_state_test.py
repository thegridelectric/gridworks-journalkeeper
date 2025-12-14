"""
Tests for enum change.valve.state.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangeValveState


def test_change_valve_state() -> None:
    assert set(ChangeValveState.values()) == {
        "OpenValve",
        "CloseValve",
    }

    assert ChangeValveState.default() == ChangeValveState.OpenValve
    assert ChangeValveState.enum_name() == "change.valve.state"
