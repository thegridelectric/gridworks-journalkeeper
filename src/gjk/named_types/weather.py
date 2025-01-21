"""Type weather, version 000"""

from typing import Literal

from gw.named_types import GwBase

from gjk.property_format import (
    LeftRightDot,
    UTCSeconds,
)


class Weather(GwBase):
    from_g_node_alias: LeftRightDot
    weather_channel_name: LeftRightDot
    unix_time_s: UTCSeconds
    outside_air_temp_f: float
    wind_speed_mph: float
    type_name: Literal["weather"] = "weather"
    version: Literal["000"] = "000"
