"""Journal `snapshot.spaceheat` at its own time and refresh the derived
operating status of a house on the old scada code."""

import logging
from datetime import UTC, datetime

from gjk.house_status_projection import HouseStatusProjection
from gjk.layouts_projection import terminal_asset_alias
from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.sema.types import SnapshotSpaceheat


class SnapshotSpaceheatPersistor:
    def __init__(self, logger: logging.Logger, projection: HouseStatusProjection):
        self.logger = logger
        self.target_message_type = "snapshot.spaceheat"
        self.fanout_on_import = False
        self.projection = projection

    def persist_v003(
        self, from_alias: str, time_received: datetime, snapshot: SnapshotSpaceheat
    ) -> MessagePersistenceInfo:
        created_at = datetime.fromtimestamp(
            snapshot.snapshot_time_unix_ms / 1000, tz=UTC
        )
        return MessagePersistenceInfo(
            id=default_message_id(from_alias, snapshot.type_name, created_at),
            created_at=created_at,
            live_only_db_operations=lambda db: self.projection.derive(
                db, terminal_asset_alias(snapshot.from_g_node_alias)
            ),
        )
