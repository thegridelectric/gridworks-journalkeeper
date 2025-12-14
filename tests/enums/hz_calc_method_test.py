"""
Tests for enum hz.calc.method.000 from the GridWorks Type Registry.
"""

from gjk.enums import HzCalcMethod


def test_hz_calc_method() -> None:
    assert set(HzCalcMethod.values()) == {
        "BasicExpWeightedAvg",
        "BasicButterWorth",
    }

    assert HzCalcMethod.default() == HzCalcMethod.BasicExpWeightedAvg
    assert HzCalcMethod.enum_name() == "hz.calc.method"
    assert HzCalcMethod.enum_version() == "000"

    assert HzCalcMethod.version("BasicExpWeightedAvg") == "000"
    assert HzCalcMethod.version("BasicButterWorth") == "000"

    for value in HzCalcMethod.values():
        symbol = HzCalcMethod.value_to_symbol(value)
        assert HzCalcMethod.symbol_to_value(symbol) == value
