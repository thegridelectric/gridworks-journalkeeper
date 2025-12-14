"""
Tests for enum change.heat.pump.control.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangeHeatPumpControl


def test_change_heat_pump_control() -> None:
    assert set(ChangeHeatPumpControl.values()) == {
        "SwitchToTankAquastat",
        "SwitchToScada",
    }

    assert ChangeHeatPumpControl.default() == ChangeHeatPumpControl.SwitchToTankAquastat
    assert ChangeHeatPumpControl.enum_name() == "change.heat.pump.control"
