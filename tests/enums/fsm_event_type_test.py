"""
Tests for enum sh.fsm.event.type.000 from the GridWorks Type Registry.
"""

from gjk.enums import FsmEventType


def test_fsm_event_type() -> None:
    assert set(FsmEventType.values()) == {
        "ChangeRelayPin",
        "ChangeRelayState",
        "SetAnalog010V",
        "SetAnalog420mA",
        "ChangeValveState",
        "ChangeStoreFlowDirection",
        "ChangeHeatcallSource",
        "ChangeAquastatControl",
        "ChangeHeatPumpControl",
        "ChangeLgOperatingMode",
        "TimerFinished",
        "ChangePrimaryPumpState",
        "ChangePrimaryPumpControl",
    }

    assert FsmEventType.default() == FsmEventType.ChangeRelayState
    assert FsmEventType.enum_name() == "sh.fsm.event.type"
    assert FsmEventType.enum_version() == "000"

    assert FsmEventType.version("ChangeRelayPin") == "000"
    assert FsmEventType.version("ChangeRelayState") == "000"
    assert FsmEventType.version("SetAnalog010V") == "000"
    assert FsmEventType.version("SetAnalog420mA") == "000"
    assert FsmEventType.version("ChangeValveState") == "000"
    assert FsmEventType.version("ChangeStoreFlowDirection") == "000"
    assert FsmEventType.version("ChangeHeatcallSource") == "000"
    assert FsmEventType.version("ChangeAquastatControl") == "000"
    assert FsmEventType.version("ChangeHeatPumpControl") == "000"
    assert FsmEventType.version("ChangeLgOperatingMode") == "000"
    assert FsmEventType.version("TimerFinished") == "000"
    assert FsmEventType.version("ChangePrimaryPumpState") == "000"
    assert FsmEventType.version("ChangePrimaryPumpControl") == "000"

    for value in FsmEventType.values():
        symbol = FsmEventType.value_to_symbol(value)
        assert FsmEventType.symbol_to_value(symbol) == value
