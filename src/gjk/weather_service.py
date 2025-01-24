"""Weather Service"""

import threading
import time
from typing import Any, Dict, Optional

import pendulum
import requests
from gw.named_types import GwBase
from gwbase.actor_base import ActorBase
from gwbase.enums import GNodeRole, MessageCategory
from result import Err, Ok, Result

from gjk.config import Settings
from gjk.named_types import Weather
from gjk.named_types.asl_types import TypeByName

KMLT_LAT = 45.6573
KMLT_LON = -68.7098
WEATHER_CHANNEL = "weather.gov.kmlt"
KMLT_STATION = "KMLT"  # ICAO code for Millinocket
BASE_URL = "https://api.weather.gov"


class WeatherResult:
    def __init__(
        self,
        success: bool,
        value: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.value = value
        self.error = error


def safe_get_nested(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    """Safely get nested dictionary value, returning None if any key is missing"""
    curr = d
    for key in keys:
        if isinstance(key, int):
            if not isinstance(curr, list) or not curr or abs(key) > len(curr):
                return None
            curr = curr[key]
        else:
            if not isinstance(curr, dict) or key not in curr:
                return None
            curr = curr[key]
    return curr


def convert_temp_c_to_f(temp_c: Optional[float]) -> Optional[float]:
    """Convert Celsius to Fahrenheit, handling None values"""
    if temp_c is None:
        return None
    return round((temp_c * 9 / 5) + 32, 2)


def convert_kmph_to_mph(speed_kmph: Optional[float]) -> Optional[float]:
    """Convert km_h-1 to miles/hour, handling None values"""
    if speed_kmph is None:
        return None
    return round(speed_kmph * 0.621371, 2)


def get_latest_observation() -> Result[WeatherResult, Exception]:
    """
    WeatherResult.success if False unless there is a reported observation
    in the last two hours, and the latest reported observation has a
    timestamp and temperature
    """
    try:
        url = f"{BASE_URL}/stations/{KMLT_STATION}/observations"
        start_time = pendulum.now("UTC").subtract(hours=2)
        end_time = pendulum.now("UTC").add(minutes=5)

        params = {
            "start": start_time.to_iso8601_string(),
            "end": end_time.to_iso8601_string(),
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            return Ok(
                WeatherResult(
                    False, error=f"Error fetching observations: {response.status_code}"
                )
            )

        data = response.json()
        features = safe_get_nested(data, "features")

        if not features:
            return Ok(WeatherResult(False, error="No observations received"))

        latest = safe_get_nested(data, "features", -1, "properties")
        if not latest:
            return Ok(WeatherResult(False, error="No properties in latest observation"))
        latest_temp = safe_get_nested(latest, "temperature", "value")
        if not latest_temp:
            return Ok(
                WeatherResult(False, error="No temperature in latest observation")
            )
        timestamp_str = safe_get_nested(latest, "timestamp")
        if not timestamp_str:
            return Ok(WeatherResult(False, error="No timestamp in latest observation"))
        return Ok(WeatherResult(True, value=latest))

    except Exception as e:
        return Err(e)


class WeatherService(ActorBase):
    def __init__(self, settings: Settings):
        settings.g_node_alias = "hw1.isone.ws"
        settings.g_node_role_value = GNodeRole.WeatherService
        super().__init__(settings=settings, type_by_name=TypeByName)
        self.settings: Settings = settings
        self._consume_exchange = "ws_tx"
        self.main_thread = threading.Thread(target=self.main)

    def local_start(self) -> None:
        self.main_thread.start()
        self._main_loop_running = True

    def local_stop(self) -> None:
        self._main_loop_running = False
        self.main_thread.join()

    def route_mqtt_message(self, from_alias: str, payload: GwBase) -> None:
        now = pendulum.now("America/New_York")
        short_alias = from_alias.split(".")[-2]
        print(
            f"[{now.format('YYYY-MM-DD HH:mm:ss.SSS')}] {payload.type_name} from {short_alias}"
        )

    def create_weather_payload(self, observation: Dict[str, Any]) -> Optional[Weather]:
        try:
            timestamp_str = safe_get_nested(observation, "timestamp")
            if not timestamp_str:
                print("Warning: No timestamp in observation")
                return None

            # Parse ISO timestamp and convert to unix timestamp
            try:
                obs_time = pendulum.parse(timestamp_str)
                observation_time = int(obs_time.timestamp())
            except Exception as e:
                print(f"Error parsing timestamp {timestamp_str}: {e}")
                return None

            temp_c = safe_get_nested(observation, "temperature", "value")
            temp_units = safe_get_nested(observation, "temperature", "unitCode")
            if temp_units != "wmoUnit:degC":
                print(f"Wind units are {temp_units}, expected wmoUnit:degC")
                return None
            temp_f = convert_temp_c_to_f(temp_c)

            wind_ms = safe_get_nested(observation, "windSpeed", "value")
            wind_units = safe_get_nested(observation, "windSpeed", "unitCode")
            if wind_units != "wmoUnit:km_h-1":
                print(f"Wind units are {wind_units}, expected wmoUnit:km_h-1!")
                return None
            wind_mph = convert_kmph_to_mph(wind_ms)

            if temp_f is None:
                print("Warning: Temperature reading was None")

            return Weather(
                from_g_node_alias=self.alias,
                weather_channel_name=WEATHER_CHANNEL,
                outside_air_temp_f=temp_f,
                wind_speed_mph=wind_mph,  # Optional in Weather type
                unix_time_s=observation_time,
            )
        except Exception as e:
            print(f"Error creating weather payload: {e}")
            return None

    def main(self) -> None:
        last_observation_time = None
        CHECK_INTERVAL_SECONDS = 600  # 10 minutes

        while self._main_loop_running:
            try:
                observation_result = get_latest_observation()
                if isinstance(observation_result, Err):
                    print(f"Error getting observation: {observation_result.err()}")
                    continue

                result = observation_result.unwrap()
                if not result.success:
                    print(f"Error getting observation: {result.error}")
                    continue
                observation = result.value
                current_observation_time = pendulum.parse(observation["timestamp"])
                if (
                    last_observation_time is None
                    or current_observation_time > last_observation_time
                ):
                    last_observation_time = current_observation_time
                    weather = self.create_weather_payload(result.value)
                    observation_time = pendulum.from_timestamp(
                        weather.unix_time_s, tz="America/New_York"
                    )
                    print(
                        f"[{observation_time.format('YYYY-MM-DD HH:mm:ss')} ET] "
                        f"{WEATHER_CHANNEL}: {weather.outside_air_temp_f}°F, "
                        f"{weather.wind_speed_mph} mph"
                    )
                    self.send_message(
                        payload=weather,
                        message_category=MessageCategory.RabbitJsonBroadcast,
                    )

                time.sleep(CHECK_INTERVAL_SECONDS)
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(60)


# How to get the station id from lat lon
# url = f"https://api.weather.gov/points/{KMLT_LAT},{KMLT_LON}"
# response = requests.get(url)
# # Get the nearest observation station (this will be KMLT)
# grid_data = response.json()
# station_url = grid_data["properties"]["observationStations"]
# station_response = requests.get(station_url)
# if station_response.status_code != 200:
#     print(f"Error fetching station data: {station_response.status_code}")
#     return
# stations = station_response.json()
# station_id = stations["features"][0]["properties"]["stationIdentifier"]