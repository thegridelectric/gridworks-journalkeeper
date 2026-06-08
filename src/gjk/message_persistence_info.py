import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from gjk.sema.property_format import UUID4Str

# Fixed namespace so the persist path can mint deterministic (uuid5) message
# ids — making re-imports of the same S3 object idempotent.
MESSAGE_ID_NAMESPACE = uuid.UUID("3f2504e0-4f89-41d3-9a0c-0305e82c3301")


def default_message_id(
    from_alias: str, type_name: str, time_received: datetime
) -> str:
    """Deterministic message id from the unique-per-object triple (matches the
    S3 filename), so re-importing a date is a true no-op via the
    (id, timestamp) PK + on_conflict_do_nothing. Shared by the default persist
    path and every custom persistor so they can't diverge."""
    persisted_ms = int(time_received.timestamp() * 1000)
    return str(
        uuid.uuid5(MESSAGE_ID_NAMESPACE, f"{from_alias}|{type_name}|{persisted_ms}")
    )


@dataclass
class MessagePersistenceInfo:
    id: UUID4Str
    created_at: datetime | None
    additional_db_operations: Callable[[Session], None] | None = None
