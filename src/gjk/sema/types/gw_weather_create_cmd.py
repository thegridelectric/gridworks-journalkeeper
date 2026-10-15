from typing import Literal
from gjk.sema.base import SemaType
from gjk.sema.types.gw_weather_channel_gt import GwWeatherChannelGt
from gjk.sema.types.gw_weather_forecast_bundle_gt import GwWeatherForecastBundleGt
from gjk.sema.types.gw_weather_forecast_channel_gt import GwWeatherForecastChannelGt
from gjk.sema.types.gw_weather_location_gt import GwWeatherLocationGt
from gjk.sema.types.gw_weather_seasonal_template_gt import GwWeatherSeasonalTemplateGt


class GwWeatherCreateCmd(SemaType):
    """Sema: https://schemas.electricity.works/types/gw.weather.create.cmd/001"""

    record: (
        GwWeatherChannelGt
        | GwWeatherForecastBundleGt
        | GwWeatherForecastChannelGt
        | GwWeatherLocationGt
        | GwWeatherSeasonalTemplateGt
    )
    proof: str | None = None
    type_name: Literal["gw.weather.create.cmd"] = "gw.weather.create.cmd"
    version: Literal["001"] = "001"
