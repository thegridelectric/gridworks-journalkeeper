"""Observed-series pseudo-channels — created when a bundle record
broadcast arrives.

A gw.weather.forecast.bundle.gt broadcast is the sign its embedded
observation channels are about to start flowing (the weather service
emits per bundle), so that is the moment gjk ensures each observed
series has a reading channel. OBSERVATION channels only — a forecast
channel never gets a reading channel (readings stay
current-weather-only; forecast messages live in the messages table).
The series is fleet-scoped, owned by no terminal asset; on today's
NOT-NULL table shape ``terminal_asset_alias`` carries the
broadcasting weather GNode's alias — the owning source, matching the
messages rows' from_alias.

No sema word covers the reading-channel row yet: the hand-built shape
here (flat name, hand-kept unit_type, magic channel_type) is retired
by ``gjk.pseudo.channel.gt`` when that word is authored — the channel
table then becomes the word's projection.
"""

import uuid
from datetime import datetime

from gw_data.db.models import ReadingChannelSql
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.pseudo_channels import PseudoChannel
from gjk.sema.enums import Gw1Unit
from gjk.sema.types import GwWeatherChannelGt, GwWeatherForecastBundleGt


def flat_channel_name(name: str) -> str:
    """The reading-channel rendering of a gw.weather channel Name
    (LeftRightDot → today's dash-separated channel-name form)."""
    return name.replace(".", "-")


class WeatherBundlePersistor:
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = GwWeatherForecastBundleGt.type_name_value()
        # Channels are durable identities, not current-state: creating
        # them from a replayed bundle is idempotent and desired.
        self.fanout_on_import = True

    def persist_v000(
        self,
        from_alias: str,
        time_received: datetime,
        bundle: GwWeatherForecastBundleGt,
    ) -> MessagePersistenceInfo:
        def ensure_channels(db: Session) -> None:
            for record in (
                bundle.temp_observation_channel,
                bundle.wind_speed_observation_channel,
            ):
                self._ensure_channel(db, from_alias, record)

        return MessagePersistenceInfo(
            # Records are durable identities: the bundle's own uuid is the
            # message id, so a replayed broadcast dedupes. No created_at —
            # records carry no message-created time by design.
            id=bundle.id,
            created_at=None,
            additional_db_operations=ensure_channels,
        )

    def _ensure_channel(
        self, db: Session, from_alias: str, record: GwWeatherChannelGt
    ) -> None:
        """Create-if-absent, keyed on (owner alias, flat name) among
        active rows — idempotent for live re-delivery and S3 re-import.
        An existing row that disagrees with the record is logged, never
        silently mutated (that disagreement is a human conversation)."""
        name = flat_channel_name(record.name)
        existing = (
            db
            .query(ReadingChannelSql)
            .filter(
                ReadingChannelSql.deactivated_date.is_(None),
                ReadingChannelSql.terminal_asset_alias == from_alias,
                ReadingChannelSql.name == name,
            )
            .first()
        )
        if existing is not None:
            if (
                existing.unit != record.unit
                or existing.unit_type != Gw1Unit.enum_name()
                or existing.channel_type != PseudoChannel.CHANNEL_TYPE
            ):
                self.logger.warning(
                    f"reading channel {name} ({from_alias}) exists with "
                    f"{existing.channel_type}:{existing.unit_type}:{existing.unit}, "
                    f"disagreeing with the {record.name} record ({record.unit}) — "
                    "leaving it untouched"
                )
            return
        db.add(
            ReadingChannelSql(
                id=uuid.uuid4(),
                name=name,
                terminal_asset_alias=from_alias,
                display_name=record.display_name,
                unit=record.unit,
                unit_type=Gw1Unit.enum_name(),
                channel_type=PseudoChannel.CHANNEL_TYPE,
            )
        )
        self.logger.info(
            f"created observed-series reading channel {name} ({from_alias})"
        )
