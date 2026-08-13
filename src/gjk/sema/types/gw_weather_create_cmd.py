from typing import Literal
from gjk.sema.base import SemaType
from gjk.sema.types.gw_weather_channel_gt import GwWeatherChannelGt
from gjk.sema.types.gw_weather_forecast_bundle_gt import GwWeatherForecastBundleGt
from gjk.sema.types.gw_weather_forecast_channel_gt import GwWeatherForecastChannelGt
from gjk.sema.types.gw_weather_location_gt import GwWeatherLocationGt


class GwWeatherCreateCmd(SemaType):
    """Sema: https://schemas.electricity.works/types/gw.weather.create.cmd/000"""

    record: (
        GwWeatherChannelGt
        | GwWeatherForecastBundleGt
        | GwWeatherForecastChannelGt
        | GwWeatherLocationGt
    )
    proof: str | None = None
    type_name: Literal["gw.weather.create.cmd"] = "gw.weather.create.cmd"
    version: Literal["000"] = "000"
