"""Tests atn.bid type, version 001"""

from gjk.enums import MarketPriceUnit, MarketQuantityUnit
from gjk.named_types import AtnBid


def test_atn_bid_generated() -> None:
    d = {
        "BidderAlias": "d1.isone.ver.keene.holly",
        "MarketSlotName": "e.rt60gate5.d1.isone.ver.keene.1667880000",
        "PqPairs": [
            {
                "PriceTimes1000": 40000,
                "QuantityTimes1000": 10000,
                "TypeName": "price.quantity.unitless",
                "Version": "000",
            }
        ],
        "InjectionIsPositive": False,
        "PriceUnit": "USDPerMWh",
        "QuantityUnit": "AvgkW",
        "SignedMarketFeeTxn": "gqRtc2lng6ZzdWJzaWeSgaJwa8Qgi1hzb1WaDzF+215cR8xmiRfUQMrnjqHtQV5PiFBAUtmConBrxCD8IT4Zu8vBAhRNsXoWF+2i6q2KyBZrPhmbDCKJD7rBBqFzxEAEp8UcTEJSyTmgw96/mCnNHKfhkdYMCD5jxWejHRmPCrR8U9z/FBVsoCGbjDTTk2L1k7n/eVlumEk/M1KSe48Jo3RocgKhdgGjdHhuiaRhcGFyhaJhbq9Nb2xseSBNZXRlcm1haWSiYXXZKWh0dHA6Ly9sb2NhbGhvc3Q6NTAwMC9tb2xseWNvL3doby13ZS1hcmUvoW3EIItYc29Vmg8xftteXEfMZokX1EDK546h7UFeT4hQQFLZoXQBonVupVZMRFRSo2ZlZc0D6KJmdlGjZ2VuqnNhbmRuZXQtdjGiZ2jEIC/iF+bI4LU6UTgG4SIxyD10PS0/vNAEa93OC5SVRFn6omx2zQQ5pG5vdGXEK01vbGx5IEluYyBUZWxlbWV0cnkgU3VydmV5b3JzIGFuZCBQdXJ2ZXlvcnOjc25kxCDHZxhdCT2TxxxZlZ/H5mIku1s4ulDm3EmU6dYKXCWEB6R0eXBlpGFjZmc=",
        "TypeName": "atn.bid",
        "Version": "001",
    }

    assert AtnBid.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, PriceUnit="unknown_enum_thing")
    assert AtnBid.from_dict(d2).price_unit == MarketPriceUnit.default()

    d2 = dict(d, QuantityUnit="unknown_enum_thing")
    assert AtnBid.from_dict(d2).quantity_unit == MarketQuantityUnit.default()