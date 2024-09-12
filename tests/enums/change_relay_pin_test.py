"""
Tests for enum change.relay.pin.000 from the GridWorks Type Registry.
"""

from gjk.enums import ChangeRelayPin


def test_change_relay_pin() -> None:
    assert set(ChangeRelayPin.values()) == {
        "DeEnergize",
        "Energize",
    }

    assert ChangeRelayPin.default() == ChangeRelayPin.DeEnergize
    assert ChangeRelayPin.enum_name() == "change.relay.pin"
