import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from gjk.sema.property_format import UUID4Str

# Fixed namespace so the persist path can mint deterministic (uuid5) message
# ids — making re-imports of the same S3 object idempotent.
MESSAGE_ID_NAMESPACE = uuid.UUID("3f2504e0-4f89-41d3-9a0c-0305e82c3301")


def default_message_id(from_alias: str, type_name: str, at: datetime) -> str:
    """Deterministic message id for a payload that carries no id of its own.

    `at` is the message's own created time when the payload has one, so the
    rabbit and S3 paths mint the same id and the (timestamp, id) key dedupes
    across them; only a payload with neither an id nor a created time falls
    back to the receipt time, which differs by path (see
    SemaMessagePersistor for the list). Shared by the default persist path and
    every custom persistor so they can't diverge.
    """
    at_ms = int(at.timestamp() * 1000)
    return str(uuid.uuid5(MESSAGE_ID_NAMESPACE, f"{from_alias}|{type_name}|{at_ms}"))


@dataclass
class MessagePersistenceInfo:
    id: UUID4Str
    created_at: datetime | None
    additional_db_operations: Callable[[Session], None] | None = None
