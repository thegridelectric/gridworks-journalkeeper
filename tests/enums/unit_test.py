"""
Tests for enum spaceheat.unit.000 from the GridWorks Type Registry.
"""

from gjk.enums import Unit


def test_unit() -> None:
    assert set(Unit.values()) == {
        "Unknown",
        "Unitless",
        "W",
        "Celcius",
        "Fahrenheit",
        "Gpm",
        "WattHours",
        "AmpsRms",
        "VoltsRms",
        "Gallons",
    }

    assert Unit.default() == Unit.Unknown
    assert Unit.enum_name() == "spaceheat.unit"
    assert Unit.enum_version() == "000"

    assert Unit.version("Unknown") == "000"
    assert Unit.version("Unitless") == "000"
    assert Unit.version("W") == "000"
    assert Unit.version("Celcius") == "000"
    assert Unit.version("Fahrenheit") == "000"
    assert Unit.version("Gpm") == "000"
    assert Unit.version("WattHours") == "000"
    assert Unit.version("AmpsRms") == "000"
    assert Unit.version("VoltsRms") == "000"
    assert Unit.version("Gallons") == "000"

    for value in Unit.values():
        symbol = Unit.value_to_symbol(value)
        assert Unit.symbol_to_value(symbol) == value
