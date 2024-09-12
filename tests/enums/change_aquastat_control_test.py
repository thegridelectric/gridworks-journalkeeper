"""
Tests for enum change.aquastat.control.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangeAquastatControl


def test_change_aquastat_control() -> None:
    assert set(ChangeAquastatControl.values()) == {
        "SwitchToBoiler",
        "SwitchToScada",
    }

    assert ChangeAquastatControl.default() == ChangeAquastatControl.SwitchToBoiler
    assert ChangeAquastatControl.enum_name() == "change.aquastat.control"
