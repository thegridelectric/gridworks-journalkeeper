"""
Tests for enum temp.calc.method.000 from the GridWorks Type Registry.
"""

from gjk.enums import TempCalcMethod


def test_temp_calc_method() -> None:
    assert set(TempCalcMethod.values()) == {
        "SimpleBetaForPico",
        "SimpleBeta",
    }

    assert TempCalcMethod.default() == TempCalcMethod.SimpleBeta
    assert TempCalcMethod.enum_name() == "temp.calc.method"
    assert TempCalcMethod.enum_version() == "000"

    assert TempCalcMethod.version("SimpleBetaForPico") == "000"
    assert TempCalcMethod.version("SimpleBeta") == "000"

    for value in TempCalcMethod.values():
        symbol = TempCalcMethod.value_to_symbol(value)
        assert TempCalcMethod.symbol_to_value(symbol) == value
