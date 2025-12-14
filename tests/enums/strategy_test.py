"""
Tests for enum spaceheat.strategy.000 from the GridWorks Type Registry.
"""

from gjk.enums import Strategy


def test_strategy() -> None:
    assert set(Strategy.values()) == {
        "Ha2Oil",
        "Ha1",
    }

    assert Strategy.default() == Strategy.Ha1
    assert Strategy.enum_name() == "spaceheat.strategy"
    assert Strategy.enum_version() == "000"

    assert Strategy.version("Ha2Oil") == "000"
    assert Strategy.version("Ha1") == "000"

    for value in Strategy.values():
        symbol = Strategy.value_to_symbol(value)
        assert Strategy.symbol_to_value(symbol) == value
