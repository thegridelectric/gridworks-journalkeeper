from typing import Literal
from pydantic import StrictInt
from gjk.sema.base import SemaType
from gjk.sema.enums import Gw1Quantity
from gjk.sema.property_format import LeftRightDot


class GwWeatherObservationReading(SemaType):
    """Sema: https://schemas.electricity.works/types/gw.weather.observation.reading/000"""

    channel_name: LeftRightDot
    quantity: Gw1Quantity
    value: StrictInt
    type_name: Literal["gw.weather.observation.reading"] = (
        "gw.weather.observation.reading"
    )
    version: Literal["000"] = "000"
