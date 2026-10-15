"""Journal `gw.alert` records at their own time.

An alert is two records with one AlertId: the Firing record, created at
RaisedMs, and the Resolved record that ends it, created at ResolvedMs.
The default path takes one created-time field per type and would stamp
both records with the raise time and derive the same id for both, so the
Resolved record would be dropped as a duplicate. This persistor reads
the created time off the record's own state, and the message id follows
from it, so the two records are two rows and each dedupes against the
S3 import of itself.
"""

import logging
from datetime import UTC, datetime

from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.sema.enums import GwAlertState
from gjk.sema.types import GwAlert


class AlertPersistor:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.target_message_type = "gw.alert"
        self.fanout_on_import = False

    @staticmethod
    def created_at(alert: GwAlert) -> datetime:
        """RaisedMs for a Firing record, ResolvedMs for a Resolved one."""
        created_ms = alert.raised_ms
        if alert.state == GwAlertState.Resolved and alert.resolved_ms is not None:
            created_ms = alert.resolved_ms
        return datetime.fromtimestamp(created_ms / 1000, tz=UTC)

    def persist_v000(
        self, from_alias: str, time_received: datetime, alert: GwAlert
    ) -> MessagePersistenceInfo:
        created_at = self.created_at(alert)
        return MessagePersistenceInfo(
            id=default_message_id(from_alias, alert.type_name, created_at),
            created_at=created_at,
        )
