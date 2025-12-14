"""
Tests for enum change.heatcall.source.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangeHeatcallSource


def test_change_heatcall_source() -> None:
    assert set(ChangeHeatcallSource.values()) == {
        "SwitchToWallThermostat",
        "SwitchToScada",
    }

    assert ChangeHeatcallSource.default() == ChangeHeatcallSource.SwitchToWallThermostat
    assert ChangeHeatcallSource.enum_name() == "change.heatcall.source"
