"""Observed-series reading channels: one ``reading_channels`` row per
``gw.weather.channel.gt`` record a weather GNode broadcasts.

The record broadcast is the moment the series exists for the journal,
whether or not any bundle binds it: a station minted for an archive
replay has channels and observations but no forecast bundle, and its
readings need a row to land on. The bundle persistor ensures the same
rows for the channels it embeds, so a bundle that arrives before its
channel records still has rows; both paths are create-if-absent on the
same key.

The series is fleet-scoped, owned by no terminal asset; on today's
NOT-NULL table shape ``terminal_asset_alias`` is the broadcasting
weather GNode's alias, matching the messages rows' from_alias.

The row is the record's index: ``channel_id`` is the record's Id, the
unit is the record's, and the kind is WeatherObserved. The station and
the rest of the record are read from the journaled record by that Id.
No sema word covers the reading-channel row itself yet: the hand-built
shape here (flat name, hand-kept unit_type) is retired by
``gjk.pseudo.channel.gt`` when that word is authored; the channel
table then becomes the word's projection.
"""

import logging
import uuid
from datetime import datetime

from gw_data.db.models import ReadingChannelSql
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.sema.enums import Gw1Unit, GwChannelKind
from gjk.sema.types import GwWeatherChannelGt


def flat_channel_name(name: str) -> str:
    """The reading-channel rendering of a gw.weather channel Name
    (LeftRightDot → today's dash-separated channel-name form)."""
    return name.replace(".", "-")


def ensure_channel(
    db: Session, logger: logging.Logger, from_alias: str, record: GwWeatherChannelGt
) -> None:
    """Create-if-absent, keyed on (owner alias, flat name) among active
    rows: idempotent for live re-delivery, S3 re-import and the bundle
    path ensuring the same channel. An existing row that disagrees with
    the record is logged, never silently mutated (that disagreement is
    a human conversation)."""
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
            or existing.channel_type != GwChannelKind.WeatherObserved.value
        ):
            logger.warning(
                f"reading channel {name} ({from_alias}) exists with "
                f"{existing.channel_type}:{existing.unit_type}:{existing.unit}, "
                f"disagreeing with the {record.name} record ({record.unit}); "
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
            channel_type=GwChannelKind.WeatherObserved.value,
            channel_id=uuid.UUID(record.id),
        )
    )
    logger.info(f"created observed-series reading channel {name} ({from_alias})")


class WeatherChannelPersistor:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.target_message_type = GwWeatherChannelGt.type_name_value()
        # Channels are durable identities, not current-state: creating
        # them from a replayed record is idempotent and desired.
        self.fanout_on_import = True

    def persist_v002(
        self,
        from_alias: str,
        time_received: datetime,
        record: GwWeatherChannelGt,
    ) -> MessagePersistenceInfo:
        return MessagePersistenceInfo(
            # Records are durable identities: the record's own uuid is the
            # message id, so a replayed broadcast dedupes. No created_at:
            # records have no message-created time by design.
            id=record.id,
            created_at=None,
            additional_db_operations=lambda db: ensure_channel(
                db, self.logger, from_alias, record
            ),
        )
