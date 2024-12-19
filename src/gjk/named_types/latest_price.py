"""Type latest.price, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import StrictInt, field_validator

from gjk.enums import MarketPriceUnit
from gjk.property_format import (
    LeftRightDot,
    UUID4Str,
    MarketSlotName
)


class LatestPrice(GwBase):
    from_g_node_alias: LeftRightDot
    price_times1000: StrictInt
    price_unit: MarketPriceUnit
    market_slot_name: MarketSlotName
    message_id: UUID4Str
    type_name: Literal["latest.price"] = "latest.price"
    version: Literal["000"] = "000"
