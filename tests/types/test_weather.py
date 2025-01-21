"""Tests weather type, version 000"""

from gjk.named_types import Weather


def test_weather_generated() -> None:
    d = {
        "FromGNodeAlias": "hw1.isone.ws",
        "WeatherChannelName": "weather.gov.kmlt",
        "UnixTimeS": 1737424800,
        "OutsideAirTempF": -7.3,
        "WindSpeedMph": 12.1,
        "TypeName": "weather",
        "Version": "000",
    }

    assert Weather.from_dict(d).to_dict() == d
