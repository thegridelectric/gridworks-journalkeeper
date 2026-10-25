"""Observed weather readings: a gw.weather.observation's values, one per
observed series, at the station's ObservationTime.

Each reading names its gw.weather.channel.gt; the journaled record of
that name from the same weather GNode gives the record Id, and the
reading_channels row whose channel_id is that Id takes the value, in
the record's unit. An observation marked Interpolated is a fabricated
fill and writes no readings: the message row keeps it, and the readings
table holds only what the station observed.
"""

import logging
import uuid
from datetime import datetime

from gw_data.db.models import MessageSql, ReadingChannelSql, ReadingSql
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.sema.types import GwWeatherChannelGt, GwWeatherObservation


class WeatherObservationPersistor:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.target_message_type = GwWeatherObservation.type_name_value()
        # Observations are history; a replay fills the readings it missed.
        self.fanout_on_import = True
        # (weather GNode alias, channel name) -> the active row's id. A
        # name with no record or no row yet is not cached, so it resolves
        # once the record and its row arrive.
        self.row_ids: dict[tuple[str, str], uuid.UUID] = {}
        self.unresolved_logged: set[tuple[str, str]] = set()

    def persist_v001(
        self,
        from_alias: str,
        time_received: datetime,
        observation: GwWeatherObservation,
    ) -> MessagePersistenceInfo:
        # The word has no created time or id, so the message row is keyed
        # on the receipt time as on the default path.
        message_id = uuid.UUID(
            default_message_id(from_alias, self.target_message_type, time_received)
        )
        return MessagePersistenceInfo(
            id=str(message_id),
            created_at=None,
            additional_db_operations=lambda db: self.add_readings(
                db, from_alias, message_id, observation
            ),
        )

    def add_readings(
        self,
        db: Session,
        from_alias: str,
        message_id: uuid.UUID,
        observation: GwWeatherObservation,
    ) -> None:
        if observation.interpolated:
            return
        timestamp = datetime.fromisoformat(observation.observation_time)
        readings = []
        for reading in observation.reading_list:
            row_id = self.row_id(db, from_alias, reading.channel_name)
            if row_id is None:
                continue
            readings.append(
                ReadingSql(
                    channel_id=row_id,
                    message_id=message_id,
                    timestamp=timestamp,
                    value=reading.value,
                )
            )
        if readings:
            stmt = pg_insert(ReadingSql).on_conflict_do_nothing(
                index_elements=["timestamp", "channel_id"]
            )
            db.execute(stmt, [r.__dict__ for r in readings])

    def row_id(
        self, db: Session, from_alias: str, channel_name: str
    ) -> uuid.UUID | None:
        key = (from_alias, channel_name)
        cached = self.row_ids.get(key)
        if cached is not None:
            return cached
        record = (
            db
            .query(MessageSql.id)
            .filter(
                MessageSql.from_alias == from_alias,
                MessageSql.message_type_name == GwWeatherChannelGt.type_name_value(),
                MessageSql.payload["Name"].astext == channel_name,
            )
            .order_by(MessageSql.timestamp.desc())
            .first()
        )
        row = (
            None
            if record is None
            else (
                db
                .query(ReadingChannelSql.id)
                .filter(
                    ReadingChannelSql.channel_id == record.id,
                    ReadingChannelSql.deactivated_date.is_(None),
                )
                .first()
            )
        )
        if row is None:
            if key not in self.unresolved_logged:
                self.unresolved_logged.add(key)
                what = (
                    "no gw.weather.channel.gt record"
                    if record is None
                    else "no reading channel row"
                )
                self.logger.warning(
                    f"observation reading on {channel_name} from {from_alias}: {what}; readings dropped until it exists"
                )
            return None
        row_id = row.id
        assert isinstance(row_id, uuid.UUID)
        self.row_ids[key] = row_id
        return row_id
