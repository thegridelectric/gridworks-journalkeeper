"""Tests power.watts type, version 000"""

from gjk.types import PowerWatts


def test_power_watts_generated() -> None:
    t = PowerWatts(
        watts=4500,
    )

    d = {
        "Watts": 4500,
        "TypeName": "power.watts",
        "Version": "000",
    }

    assert t.to_dict() == d
    assert t == PowerWatts.from_dict(d)
