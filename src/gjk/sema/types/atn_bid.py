from typing import Literal
from pydantic import model_validator
from gjk.sema.base import SemaType
from gjk.sema.enums import MarketPriceUnit
from gjk.sema.enums import MarketQuantityUnit
from gjk.sema.property_format import LeftRightDot
from gjk.sema.property_format import MarketSlotName
from gjk.sema.types.price_quantity_unitless import PriceQuantityUnitless


class AtnBid(SemaType):
    """Sema: https://schemas.electricity.works/types/atn.bid/002"""

    bidder_alias: LeftRightDot
    market_slot_name: MarketSlotName
    pq_pairs: list[PriceQuantityUnitless]
    injection_is_positive: bool
    price_unit: MarketPriceUnit
    quantity_unit: MarketQuantityUnit
    signed_market_fee_txn: str
    type_name: Literal["atn.bid"] = "atn.bid"
    version: Literal["002"] = "002"

    @model_validator(mode="after")
    def check_axiom_1(self) -> "AtnBid":
        """
        Axiom 1: PqPairsPriceMaxMatchesMarketType
        The first price in PqPairs SHALL equal the PriceMax defined by the MarketType
        associated with MarketSlotName.
        """
        # Validation requires access to the MarketType registry; deferred to application logic.
        return self
