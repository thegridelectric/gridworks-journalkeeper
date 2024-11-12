"""
Tests for enum change.store.flow.relay.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangeStoreFlowRelay


def test_change_store_flow_relay() -> None:
    assert set(ChangeStoreFlowRelay.values()) == {
        "DischargeStore",
        "ChargeStore",
    }

    assert ChangeStoreFlowRelay.default() == ChangeStoreFlowRelay.DischargeStore
    assert ChangeStoreFlowRelay.enum_name() == "change.store.flow.relay"
    assert ChangeStoreFlowRelay.enum_version() == "000"

    assert ChangeStoreFlowRelay.version("DischargeStore") == "000"
    assert ChangeStoreFlowRelay.version("ChargeStore") == "000"

    for value in ChangeStoreFlowRelay.values():
        symbol = ChangeStoreFlowRelay.value_to_symbol(value)
        assert ChangeStoreFlowRelay.symbol_to_value(symbol) == value
