"""Tests ha1.params type, version 001"""

from gjk.named_types import Ha1Params


def test_ha1_params_generated() -> None:
    d = {
        "AlphaTimes10": 120,
        "BetaTimes100": -22,
        "GammaEx6": 0,
        "IntermediatePowerKw": 1.5,
        "IntermediateRswtF": 100,
        "DdPowerKw": 12,
        "DdRswtF": 160,
        "DdDeltaTF": 20,
        "HpMaxKwTh": 6,
        "MaxEwtF": 170,
        "TypeName": "ha1.params",
        "Version": "001",
    }

    assert Ha1Params.from_dict(d).to_dict() == d
