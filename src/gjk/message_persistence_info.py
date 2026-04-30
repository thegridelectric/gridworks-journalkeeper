from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sema.runtime.property_format import UUID4Str
from sqlalchemy.orm import Session


@dataclass
class MessagePersistenceInfo:
    id: UUID4Str
    created_at: datetime
    additional_db_operations: Callable[[Session], None] | None
