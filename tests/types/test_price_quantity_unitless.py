"""Tests price.quantity.unitless type, version 000"""

from gjk.named_types import PriceQuantityUnitless


def test_price_quantity_unitless_generated() -> None:
    d = {
        "PriceX1000": 40000,
        "QuantityX1000": 10000,
        "TypeName": "price.quantity.unitless",
        "Version": "001",
    }

    assert PriceQuantityUnitless.from_dict(d).to_dict() == d
