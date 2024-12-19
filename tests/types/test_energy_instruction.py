"""Tests energy.instruction type, version 000"""

from gjk.named_types import EnergyInstruction


def test_energy_instruction_generated() -> None:
    d = {
        "FromGNodeAlias": "d1.isone.me.versant.keene.orange",
        "SlotStartS": 1733421600,
        "SlotDurationMinutes": 60,
        "SendTimeMs": 1733421602300,
        "AvgPowerWatts": 9000,
        "TypeName": "energy.instruction",
        "Version": "000",
    }

    assert EnergyInstruction.from_dict(d).to_dict() == d