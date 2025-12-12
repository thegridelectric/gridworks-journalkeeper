"""Type price.quantity.unitless, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import StrictInt


class PriceQuantityUnitless(GwBase):
    price_x1000: StrictInt
    quantity_x1000: StrictInt
    type_name: Literal["price.quantity.unitless"] = "price.quantity.unitless"
    version: Literal["001"] = "001"
