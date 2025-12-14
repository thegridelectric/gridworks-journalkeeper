"""Tests weather.forecast type, version 000"""

from gjk.named_types import WeatherForecast


def test_weather_forecast_generated() -> None:
    d = {
        "FromGNodeAlias": "hw1.isone.ps",
        "WeatherChannelName": "weather.gov.kmlt",
        "Time": [1735938000],
        "OatF": [13.5],
        "WindSpeedMph": [0],
        "WeatherUid": "7d4dd88e-04a3-4d61-92e0-49b1cd6cfda6",
        "ForecastCreatedS": 1735936266,
        "TypeName": "weather.forecast",
        "Version": "000",
    }

    assert WeatherForecast.from_dict(d).to_dict() == d
