"""Type atn.bid, version 001"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import field_validator, model_validator
from typing_extensions import Self

from gjk.enums import MarketPriceUnit, MarketQuantityUnit
from gjk.named_types.price_quantity_unitless import PriceQuantityUnitless
from gjk.property_format import (
    LeftRightDot,
    MarketSlotName

)


class AtnBid(GwBase):
    bidder_alias: LeftRightDot
    market_slot_name: MarketSlotName
    pq_pairs: List[PriceQuantityUnitless]
    injection_is_positive: bool
    price_unit: MarketPriceUnit
    quantity_unit: MarketQuantityUnit
    signed_market_fee_txn: str
    type_name: Literal["atn.bid"] = "atn.bid"
    version: Literal["001"] = "001"

    @field_validator("signed_market_fee_txn")
    @classmethod
    def _check_signed_market_fee_txn(cls, v: str) -> str:
        # eventually check_is_algo_msg_pack_encoded(v)
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: PqPairs PriceMax matches MarketType.
        There is a GridWorks global list of MarketTypes (a GridWorks type), identified by their MarketTypeNames (a GridWorks enum).  The MarketType has a PriceMax, which must be the first price of the first PriceQuantity pair in PqPairs.
        """
        # Implement check for axiom 1"
        return self
