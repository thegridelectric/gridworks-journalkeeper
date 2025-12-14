"""
Tests for enum relay.wiring.config.000 from the GridWorks Type Registry.
"""

from gjk.enums import RelayWiringConfig


def test_relay_wiring_config() -> None:
    assert set(RelayWiringConfig.values()) == {
        "NormallyClosed",
        "NormallyOpen",
        "DoubleThrow",
    }

    assert RelayWiringConfig.default() == RelayWiringConfig.NormallyClosed
    assert RelayWiringConfig.enum_name() == "relay.wiring.config"
    assert RelayWiringConfig.enum_version() == "000"

    assert RelayWiringConfig.version("NormallyClosed") == "000"
    assert RelayWiringConfig.version("NormallyOpen") == "000"
    assert RelayWiringConfig.version("DoubleThrow") == "000"

    for value in RelayWiringConfig.values():
        symbol = RelayWiringConfig.value_to_symbol(value)
        assert RelayWiringConfig.symbol_to_value(symbol) == value
