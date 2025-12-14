"""Type power.watts, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import StrictInt


class PowerWatts(GwBase):
    watts: StrictInt
    type_name: Literal["power.watts"] = "power.watts"
    version: Literal["000"] = "000"
