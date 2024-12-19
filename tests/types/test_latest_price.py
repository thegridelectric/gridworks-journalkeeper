"""Tests latest.price type, version 000"""

from gjk.enums import MarketPriceUnit
from gjk.named_types import LatestPrice


def test_latest_price_generated() -> None:
    d = {
        "FromGNodeAlias": "d1.isone.ver.keene",
        "PriceTimes1000": 32134,
        "PriceUnit": "USDPerMWh",
        "MarketSlotName": "e.rt60gate5.d1.isone.ver.keene.1577854800",
        "MessageId": "03d27b8e-f6b3-40c5-afe8-880d12921710",
        "TypeName": "latest.price",
        "Version": "000",
    }

    assert LatestPrice.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, PriceUnit="unknown_enum_thing")
    assert LatestPrice.from_dict(d2).price_unit == MarketPriceUnit.default()
