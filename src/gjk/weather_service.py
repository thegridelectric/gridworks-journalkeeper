"""Weather Service Hack"""

import threading
import time
from datetime import datetime, timedelta, timezone
import requests
import pendulum
import pytz
from gw.enums import MessageCategory
from gw.named_types import GwBase
from gwbase.actor_base import ActorBase
from gwbase.enums import GNodeRole

from gjk.config import Settings
from gjk.named_types import (
    Weather,
)
from gjk.named_types.asl_types import TypeByName

KMLT_LAT = 45.6573
KMLT_LON = -68.7098
WEATHER_CHANNEL = "weather.gov.kmlt"

def to_fahrenheit(t):
    return (t * 9/5) + 32

def to_mph(ws):
    return ws * 0.621371


class WeatherService(ActorBase):
    def __init__(self, settings: Settings):
        settings.g_node_alias = "hw1.isone.ws"
        settings.g_node_role_value = GNodeRole.WeatherService
        super().__init__(settings=settings, type_by_name=TypeByName)
        self.settings: Settings = settings
        self._consume_exchange = "ws_tx"
        self.main_thread = threading.Thread(target=self.main)

    def local_start(self) -> None:
        """This overwrites local_start in actor_base, used for additional threads.
        It cannot assume the rabbit channels are established and that
        messages can be received or sent."""
        self.main_thread.start()
        self._main_loop_running = True

    def local_stop(self) -> None:
        self._main_loop_running = False
        self.main_thread.join()

    ########################f
    ## Receives
    ########################

    def route_mqtt_message(self, from_alias: str, payload: GwBase) -> None:
        t = time.time()
        ft = pendulum.from_timestamp(t, tz="America/New_York").format(
            "YYYY-MM-DD HH:mm:ss.SSS"
        )
        short_alias = from_alias.split(".")[-2]
        print(f"[{ft}] {payload.type_name} from {short_alias}")
        # TODO: route messages when weather service listens to anything

    def main(self) -> None:
        while True:
            now = datetime.now()
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            sleep_duration = (next_hour - now).total_seconds() + 1
            print(
                f"sleeping for {int(sleep_duration / 60)} minutes before broadcasting weather"
            )
            time.sleep(sleep_duration)
            self.get_and_send_weather()

    def get_and_send_weather(self):
        """
        Use requests for now. At some point will need to figure
        out how to make the rabbit actors integrate with async.

        But this one only has one task.
        """
        # kmlt is the ICAO code for Millinocket
        url = f"https://api.weather.gov/points/{KMLT_LAT},{KMLT_LON}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching grid data: {response.status_code}")
            return

        # Get the nearest observation station (this will be KMLT)
        grid_data = response.json()
        station_url = grid_data['properties']['observationStations']
        station_response = requests.get(station_url)
        if station_response.status_code != 200:
            print(f"Error fetching station data: {station_response.status_code}")
            return
        stations = station_response.json()
        station_id = stations['features'][0]['properties']['stationIdentifier']

        # Get hourly observations from the station
        observations_url = f"https://api.weather.gov/stations/{station_id}/observations"
        start_time = time.time() - 60*60
        end_time = time.time() + 5*60
        params = {
            'start': datetime.fromtimestamp(start_time, tz=timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            'end': datetime.fromtimestamp(end_time, tz=timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }
        observations_response = requests.get(observations_url, params=params)
        if observations_response.status_code != 200:
            print(f"Error fetching observations data: {observations_response.status_code}")
            return
        observations = observations_response.json()
        if not observations:
            print("Received no observations")
            return
        # Take the latest observation
        time_observed = observations['features'][-1]['properties']['timestamp']
        time_observed = datetime.fromisoformat(time_observed).astimezone(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')
        oat_observed = round(to_fahrenheit(observations['features'][-1]['properties']['temperature']['value']),2)
        wind_speed_observed = round(to_mph(observations['features'][-1]['properties']['windSpeed']['value']),2)
        print(f"\nTime of latest observation: {time_observed}")
        print(f"OAT: {oat_observed}, WS: {wind_speed_observed}")

        # Hack to send at the top of the hour
        t = int(time.time())
        observation_time = t - (t % 3600)
        weather = Weather(
            from_g_node_alias=self.alias,
            weather_channel_name=WEATHER_CHANNEL,
            outside_air_temp_f=oat_observed,
            wind_speed_mph=wind_speed_observed,
            unix_time_s=observation_time,
        )
        observation_start = datetime.fromtimestamp(
            observation_time, tz=pytz.timezone("America/New_York")
        )
        ft = f"{observation_start.strftime('%Y-%m-%d %H:%M:%S')} ET"
        print(
            f"[{ft}] {WEATHER_CHANNEL}:  {weather.outside_air_temp_f} F, {weather.wind_speed_mph} mph"
        )

        # Use this one when you've got the pipes working
        # self.send_message(
        #     payload=weather,
        #     message_category=MessageCategory.RabbitJsonBroadcast,
        # )

        # # DON'T USE THIS ONE YET.
        # # TODO for jess: fix brken broadcast radio channel routing key
        # # from rjb.hw1-isone-ws.ws.weather.weather.gov.kmlt TO
        # # rjb.hw1-isone-ws.ws.weather.weather-gov-kmlt
        # # self.send_message(
        # #     payload=weather,
        # #     message_category=MessageCategory.RabbitJsonBroadcast,
        # #     radio_channel=WEATHER_CHANNEL,
        # # )
