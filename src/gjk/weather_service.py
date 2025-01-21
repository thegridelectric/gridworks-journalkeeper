"""Weather Service Hack"""
import logging
import threading
import time
from datetime import datetime, timedelta

import pendulum
from gw.named_types import GwBase
from gwbase.actor_base import ActorBase
from gwbase.enums import GNodeRole, MessageCategory

from gjk.config import Settings
from gjk.named_types import (
    Weather,
)
from gjk.named_types.asl_types import TypeByName

LOG_FORMAT = (
    "%(levelname) -10s %(sasctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)

class WeatherService(ActorBase):
    def __init__(self, settings: Settings):
        settings.g_node_alias = "hw1.isone.ws"
        settings.g_node_role_value = GNodeRole.WeatherService
        super().__init__(settings=settings, type_by_name=TypeByName)
        self.settings: Settings = settings
        self._consume_exchange = "ws_tx"
        self.main_thread = threading.Thread(target=self.main)

    def local_rabbit_startup(self) -> None:
        """Overwrites base class method.
        Meant for adding addtional bindings"""
        # Will eventually create types for agents to
        # ask for the names of weather broadcast channels here
        type_names = [
        ]
        routing_keys = [f"#.{tn.replace(".", "-")}" for tn in type_names]
        for rk in routing_keys:
            LOGGER.info(
                "Binding %s to %s with %s",
                self._consume_exchange,
                "ear_tx",
                rk,
            )
            self._single_channel.queue_bind(
                self.queue_name,
                "ear_tx",
                routing_key=rk,
            )

    def local_start(self) -> None:
        """This overwrites local_start in actor_base, used for additional threads.
        It cannot assume the rabbit channels are established and that
        messages can be received or sent."""
        self.main_thread.start()
        self._main_loop_running = True
        print("Just started main thread")

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
            time.sleep(sleep_duration)
            # self.get_and_send_weather()

    def get_and_send_weather(self):
        """
        Use requests for now. At some point will need to figure
        out how to make the rabbit actors integrate with async.

        But this one only has one task.
        """
        # kmlt is the ICAO code for Millinocket
        KMLT_LAT = 45.6573
        KMLT_LON = -68.7098
        WEATHER_CHANNEL =  "weather.gov.kmlt"
        url = f"https://api.weather.gov/points/{KMLT_LAT},{KMLT_LON}"

        #Hack to send at the top of the hour
        t = int(time.time())
        forecast_time = t - (t % 3600)
        payload = Weather(
            from_g_node_alias=self.alias,
            weather_channel_name=WEATHER_CHANNEL,
            outside_air_temp_f=32.2,
            wind_speed_mph=10.3,
            unix_time_s=forecast_time
        )
        forecast_start = datetime.fromtimestamp(self.weather_forecast.Time[0], tz="America/New_York")
        LOGGER.info(f"Broadcasting weather {WEATHER_CHANNEL} at {forecast_start.strftime('%Y-%m-%d %H:%M:%S')} ET")
        self.send_message(payload=payload,
                          message_category=MessageCategory.RabbitJsonBroadcast,
                          radio_channel=WEATHER_CHANNEL)
