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


# Fixed namespace for the ids of pseudo channels, which no layout names: the
# same definition for a terminal asset is the same row across layouts.
PSEUDO_CHANNEL_ID_NAMESPACE = uuid.UUID("7a1e0c5d-2b64-4f3e-9d0a-5c1b8e6f2a41")


def pseudo_channel_id(
    terminal_asset_alias: str, name: str, unit_type: str, unit: str
) -> uuid.UUID:
    """The reading_channels id of a pseudo channel: a uuid5 of its definition."""
    return uuid.uuid5(
        PSEUDO_CHANNEL_ID_NAMESPACE,
        f"{terminal_asset_alias}|{name}|{unit_type}|{unit}",
    )


@dataclass
class MessagePersistenceInfo:
    id: UUID4Str
    created_at: datetime | None
    additional_db_operations: Callable[[Session], None] | None = None
    # A current-state projection fed by this message: runs only when the
    # message arrives live from the broker, never on a persistent-store
    # replay, whatever the persistor's fanout_on_import says about
    # additional_db_operations.
    live_only_db_operations: Callable[[Session], None] | None = None
