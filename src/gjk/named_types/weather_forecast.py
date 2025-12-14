"""Type weather.forecast, version 000"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import model_validator
from typing_extensions import Self

from gjk.property_format import (
    LeftRightDot,
    UTCSeconds,
    UUID4Str,
)


class WeatherForecast(GwBase):
    from_g_node_alias: LeftRightDot
    weather_channel_name: LeftRightDot
    time: List[UTCSeconds]
    oat_f: List[float]
    wind_speed_mph: List[float]
    weather_uid: UUID4Str
    forecast_created_s: UTCSeconds
    type_name: Literal["weather.forecast"] = "weather.forecast"
    version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Length of all the lists (Time, OatF, WindspeedMph) must be the same.
        """
        # Implement check for axiom 1"
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: ForecastCreatedS is less than the first second in Time.
        """
        # Implement check for axiom 2"
        return self
