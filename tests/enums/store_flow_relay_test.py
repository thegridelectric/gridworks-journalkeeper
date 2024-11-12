"""
Tests for enum store.flow.relay.000 from the GridWorks Type Registry.
"""

from gjk.enums import StoreFlowRelay


def test_store_flow_relay() -> None:
    assert set(StoreFlowRelay.values()) == {
        "DischargingStore",
        "ChargingStore",
    }

    assert StoreFlowRelay.default() == StoreFlowRelay.DischargingStore
    assert StoreFlowRelay.enum_name() == "store.flow.relay"
    assert StoreFlowRelay.enum_version() == "000"

    assert StoreFlowRelay.version("DischargingStore") == "000"
    assert StoreFlowRelay.version("ChargingStore") == "000"

    for value in StoreFlowRelay.values():
        symbol = StoreFlowRelay.value_to_symbol(value)
        assert StoreFlowRelay.symbol_to_value(symbol) == value
