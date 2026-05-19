from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from gjk.sema.property_format import UUID4Str


@dataclass
class MessagePersistenceInfo:
    id: UUID4Str
    created_at: datetime | None
    additional_db_operations: Callable[[Session], None] | None = None
