from typing import Literal

from pydantic import StrictInt

from gjk.sema.base import SemaType
from gjk.sema.enums import MarketPriceUnit
from gjk.sema.property_format import LeftRightDot, MarketSlotName, UUID4Str


class LatestPrice(SemaType):
    """Sema: https://schemas.electricity.works/types/latest.price/000"""

    from_g_node_alias: LeftRightDot
    price_times1000: StrictInt
    price_unit: MarketPriceUnit
    market_slot_name: MarketSlotName
    message_id: UUID4Str
    type_name: Literal["latest.price"] = "latest.price"
    version: Literal["000"] = "000"
