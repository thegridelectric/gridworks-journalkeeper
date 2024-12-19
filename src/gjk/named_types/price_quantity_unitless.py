"""Type price.quantity.unitless, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import StrictInt


class PriceQuantityUnitless(GwBase):
    price_times1000: StrictInt
    quantity_times1000: StrictInt
    type_name: Literal["price.quantity.unitless"] = "price.quantity.unitless"
    version: Literal["000"] = "000"
