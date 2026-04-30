import uuid
from datetime import datetime, timezone

from gw_data.db.models import ReadingChannelSql, ReadingSql
from sema.runtime.types import ReportEvent
from sema.runtime.types.old_versions.report_event_002 import ReportEvent002
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo


class ReportEventPersistor:
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "report.event"

    def persist_readings(
        self, db: Session, from_alias: str, reportEvent: ReportEvent | ReportEvent002
    ):
        from_terminal_asset_alias = from_alias.split(".scada")[0] + ".ta"
        db_channels = (
            db.query(ReadingChannelSql)
            .filter(
                ReadingChannelSql.deactivated_date.is_(None),
                ReadingChannelSql.terminal_asset_alias == from_terminal_asset_alias,
            )
            .all()
        )

        db_channel_ids_by_name = {c.name: c.id for c in db_channels}
        readings = []
        for ch_readings in reportEvent.report.channel_reading_list:
            db_channel_id = db_channel_ids_by_name.get(ch_readings.channel_name)
            if db_channel_id is None:
                continue
            else:
                # Reports can duplicate the same timestamp and value, so we need to de-duplicate it.
                readings_by_ts = {}
                for ts, value in zip(
                    ch_readings.scada_read_time_unix_ms_list,
                    ch_readings.value_list,
                    strict=True,
                ):
                    if ts not in readings_by_ts:
                        readings_by_ts[ts] = ReadingSql(
                            channel_id=db_channel_id,
                            message_id=uuid.UUID(reportEvent.message_id),
                            timestamp=datetime.fromtimestamp(ts / 1000, timezone.utc),
                            value=value,
                        )

                readings.extend(readings_by_ts.values())

        dicts = [r.__dict__ for r in readings]
        stmt = insert(ReadingSql).on_conflict_do_nothing(
            index_elements=["timestamp", "channel_id"]
        )
        db.execute(stmt, dicts)

    def persist_v002(self, from_alias: str, report: ReportEvent002):
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
            ),
        )

    def persist_v003(self, from_alias: str, report: ReportEvent):
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
            ),
        )
