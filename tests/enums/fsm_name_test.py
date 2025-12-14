"""
Tests for enum sh.fsm.name.000 from the GridWorks Type Registry.
"""

from gjk.enums import FsmName


def test_fsm_name() -> None:
    assert set(FsmName.values()) == {
        "Unknown",
        "StoreFlowDirection",
        "RelayState",
        "RelayPinState",
    }

    assert FsmName.default() == FsmName.StoreFlowDirection
    assert FsmName.enum_name() == "sh.fsm.name"
    assert FsmName.enum_version() == "000"

    assert FsmName.version("Unknown") == "000"
    assert FsmName.version("StoreFlowDirection") == "000"
    assert FsmName.version("RelayState") == "000"
    assert FsmName.version("RelayPinState") == "000"

    for value in FsmName.values():
        symbol = FsmName.value_to_symbol(value)
        assert FsmName.symbol_to_value(symbol) == value
