"""
Tests for enum store.flow.direction.000 from the GridWorks Type Registry.
"""

from gjk.enums import StoreFlowDirection


def test_store_flow_direction() -> None:
    assert set(StoreFlowDirection.values()) == {
        "ValvedtoDischargeStore",
        "ValvesMovingToCharging",
        "ValvedtoChargeStore",
        "ValvesMovingToDischarging",
    }

    assert StoreFlowDirection.default() == StoreFlowDirection.ValvedtoDischargeStore
    assert StoreFlowDirection.enum_name() == "store.flow.direction"
