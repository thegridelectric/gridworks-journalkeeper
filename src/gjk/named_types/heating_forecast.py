"""Type heating.forecast, version 000"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import model_validator
from typing_extensions import Self

from gjk.property_format import (
    LeftRightDot,
    UTCSeconds,
    UUID4Str,
)


class HeatingForecast(GwBase):
    from_g_node_alias: LeftRightDot
    time: List[UTCSeconds]
    avg_power_kw: List[float]
    rswt_f: List[float]
    rswt_delta_t_f: List[float]
    weather_uid: UUID4Str
    forecast_created_s: UTCSeconds
    type_name: Literal["heating.forecast"] = "heating.forecast"
    version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Length of all the lists must be the same.
        """
        # Implement check for axiom 1"
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: .
        """
        # Implement check for axiom 2"
        return self
