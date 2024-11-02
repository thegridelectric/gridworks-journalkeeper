"""
Tests for enum gpm.from.hz.method.000 from the GridWorks Type Registry.
"""

from gjk.enums import GpmFromHzMethod


def test_gpm_from_hz_method() -> None:
    assert set(GpmFromHzMethod.values()) == {
        "Constant",
    }

    assert GpmFromHzMethod.default() == GpmFromHzMethod.Constant
    assert GpmFromHzMethod.enum_name() == "gpm.from.hz.method"
    assert GpmFromHzMethod.enum_version() == "000"

    assert GpmFromHzMethod.version("Constant") == "000"

    for value in GpmFromHzMethod.values():
        symbol = GpmFromHzMethod.value_to_symbol(value)
        assert GpmFromHzMethod.symbol_to_value(symbol) == value
