"""The bundle broadcast ensures the observed-series reading channels it
binds.

A gw.weather.forecast.bundle.gt broadcast embeds its observation
channel records, so the journal ensures each has a reading channel
when the bundle arrives, through the same create-if-absent path the
channel record's own broadcast takes (``weather_channel_persistor``).
OBSERVATION channels only: a forecast channel never gets a reading
channel (readings stay current-weather-only; forecast messages live
in the messages table).
"""

from datetime import datetime

from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.sema.types import GwWeatherForecastBundleGt
from gjk.weather_channel_persistor import ensure_channel


class WeatherBundlePersistor:
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = GwWeatherForecastBundleGt.type_name_value()
        # Channels are durable identities, not current-state: creating
        # them from a replayed bundle is idempotent and desired.
        self.fanout_on_import = True

    def persist_v002(
        self,
        from_alias: str,
        time_received: datetime,
        bundle: GwWeatherForecastBundleGt,
    ) -> MessagePersistenceInfo:
        def ensure_channels(db: Session) -> None:
            for binding in bundle.binding_list:
                ensure_channel(db, self.logger, from_alias, binding.observation_channel)

        return MessagePersistenceInfo(
            # Records are durable identities: the bundle's own uuid is the
            # message id, so a replayed broadcast dedupes. No created_at:
            # records have no message-created time by design.
            id=bundle.id,
            created_at=None,
            additional_db_operations=ensure_channels,
        )
