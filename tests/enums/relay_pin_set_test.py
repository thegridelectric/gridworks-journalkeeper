"""
Tests for enum relay.pin.set.000 from the GridWorks Type Registry.
"""

from gjk.enums import RelayPinSet


def test_relay_pin_set() -> None:
    assert set(RelayPinSet.values()) == {
        0,
        1,
    }

    assert RelayPinSet.default() == RelayPinSet.DeEnergized
    assert RelayPinSet.enum_name() == "relay.pin.set"
