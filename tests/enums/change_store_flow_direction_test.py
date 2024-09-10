"""
Tests for enum change.store.flow.direction.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangeStoreFlowDirection


def test_change_store_flow_direction() -> None:
    assert set(ChangeStoreFlowDirection.values()) == {
        "Discharge",
        "Charge",
    }

    assert ChangeStoreFlowDirection.default() == ChangeStoreFlowDirection.Discharge
    assert ChangeStoreFlowDirection.enum_name() == "change.store.flow.direction"
