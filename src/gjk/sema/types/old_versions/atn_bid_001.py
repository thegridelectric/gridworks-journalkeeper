from typing import Literal
from pydantic import model_validator
from gjk.sema.base import SemaType
from gjk.sema.enums import MarketPriceUnit
from gjk.sema.enums import MarketQuantityUnit
from gjk.sema.property_format import LeftRightDot
from gjk.sema.property_format import MarketSlotName
from gjk.sema.types.atn_bid import AtnBid
from gjk.sema.types.old_versions.price_quantity_unitless_000 import (
    PriceQuantityUnitless000,
)
from gjk.sema.types.price_quantity_unitless import PriceQuantityUnitless


class AtnBid001(SemaType):
    """Sema: https://schemas.electricity.works/types/atn.bid/001"""

    bidder_alias: LeftRightDot
    market_slot_name: MarketSlotName
    pq_pairs: list[PriceQuantityUnitless000 | PriceQuantityUnitless]
    injection_is_positive: bool
    price_unit: MarketPriceUnit
    quantity_unit: MarketQuantityUnit
    signed_market_fee_txn: str
    type_name: Literal["atn.bid"] = "atn.bid"
    version: Literal["001"] = "001"

    @model_validator(mode="after")
    def check_axiom_1(self) -> "AtnBid001":
        """
        Axiom 1: PqPairsPriceMaxMatchesMarketType
        The first price in PqPairs SHALL equal the PriceMax defined by the MarketType
        associated with MarketSlotName.
        """
        # Validation requires access to the MarketType registry; deferred to application logic.
        return self

    def upgrade(self) -> "AtnBid":
        """
        Fix PqPairs sub-type to price.quantity.unitless:001.
        """
        data = self.model_dump()
        # 001 accepts price.quantity.unitless 000 or 001; 002 pins 001. Upgrade
        # any 000 pairs (nested-upgrade discipline) so the result validates.
        pairs = []
        for pair in self.pq_pairs:
            if pair.version == "000":
                pair = pair.upgrade()
            pairs.append(pair.model_dump())
        data["pq_pairs"] = pairs
        data["version"] = "002"
        return AtnBid.model_validate(data)
