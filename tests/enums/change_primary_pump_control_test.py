"""
Tests for enum change.primary.pump.control.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangePrimaryPumpControl


def test_change_primary_pump_control() -> None:
    assert set(ChangePrimaryPumpControl.values()) == {
        "SwitchToScada",
        "SwitchToHeatPump",
    }

    assert (
        ChangePrimaryPumpControl.default() == ChangePrimaryPumpControl.SwitchToHeatPump
    )
    assert ChangePrimaryPumpControl.enum_name() == "change.primary.pump.control"
