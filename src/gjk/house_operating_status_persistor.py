"""Journal `gw.house.operating.status` and project it as the house's current status."""

import logging
from datetime import UTC, datetime

from gjk.house_status_projection import HouseStatusProjection
from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.sema.types import GwHouseOperatingStatus


class HouseOperatingStatusPersistor:
    def __init__(self, logger: logging.Logger, projection: HouseStatusProjection):
        self.logger = logger
        self.target_message_type = "gw.house.operating.status"
        self.fanout_on_import = False
        self.projection = projection

    def persist_v000(
        self, from_alias: str, time_received: datetime, status: GwHouseOperatingStatus
    ) -> MessagePersistenceInfo:
        created_at = datetime.fromtimestamp(status.created_ms / 1000, tz=UTC)
        message_id = default_message_id(from_alias, status.type_name, created_at)
        return MessagePersistenceInfo(
            id=message_id,
            created_at=created_at,
            live_only_db_operations=lambda db: self.projection.project_reported(
                db, from_alias, status, message_id
            ),
        )
