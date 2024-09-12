"""
Tests for enum change.lg.operating.mode.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangeLgOperatingMode


def test_change_lg_operating_mode() -> None:
    assert set(ChangeLgOperatingMode.values()) == {
        "SwitchToDhw",
        "SwitchToHeat",
    }

    assert ChangeLgOperatingMode.default() == ChangeLgOperatingMode.SwitchToHeat
    assert ChangeLgOperatingMode.enum_name() == "change.lg.operating.mode"
