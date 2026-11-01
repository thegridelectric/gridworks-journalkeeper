"""A gw.weather.forecast is journaled to the messages table under the
identity that tells one bundle's emission from another's: the weather
service sends every bundle it serves in one slot, from one alias at one
MessageCreatedMs, so the sender and time alone name several messages.
At 002 the forecast's own ForecastUid is the row id. At 001, which has
no id, the row id is the uuid5 of sender, type, bundle name and created
time."""

from datetime import UTC, datetime

from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.sema.types import GwWeatherForecast
from gjk.sema.types.old_versions.gw_weather_forecast_001 import GwWeatherForecast001


class GwWeatherForecastPersistor:
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = GwWeatherForecast.type_name_value()
        self.fanout_on_import = True

    def persist_v001(
        self, from_alias: str, time_received: datetime, forecast: GwWeatherForecast001
    ) -> MessagePersistenceInfo:
        created_at = datetime.fromtimestamp(forecast.message_created_ms / 1000, tz=UTC)
        return MessagePersistenceInfo(
            id=default_message_id(
                from_alias,
                forecast.type_name,
                created_at,
                subject=forecast.bundle_name,
            ),
            created_at=created_at,
        )

    def persist_v002(
        self, from_alias: str, time_received: datetime, forecast: GwWeatherForecast
    ) -> MessagePersistenceInfo:
        return MessagePersistenceInfo(
            id=forecast.forecast_uid,
            created_at=datetime.fromtimestamp(
                forecast.message_created_ms / 1000, tz=UTC
            ),
        )
