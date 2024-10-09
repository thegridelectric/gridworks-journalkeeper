"""Type power.watts, version 000"""

from typing import Literal

from pydantic import StrictInt

from gjk.types.gw_base import GwBase


class PowerWatts(GwBase):
    watts: StrictInt
    type_name: Literal["power.watts"] = "power.watts"
    version: Literal["000"] = "000"
