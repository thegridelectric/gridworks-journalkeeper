from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError

from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UUID4Str,
)


class Message(BaseModel):
    message_id: UUID4Str
    from_alias: LeftRightDot
    message_type_name: LeftRightDot
    message_persisted_ms: UTCMilliseconds
    payload: dict
    message_created_ms: UTCMilliseconds | None = None

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        populate_by_name=True,
    )

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        return d

    def to_sql_dict(self) -> dict[str, Any]:
        d = self.model_dump()


        d['id'] = uuid.UUID(d['id'])
        d['persisted_at'] = datetime.fromtimestamp(d.pop('message_persisted_ms'), timezone.utc)

        created_ms = d.pop('message_created_ms', None)
        if created_ms is None:
            d['created_at'] = None
            d[['timestamp']] = d['persisted_at']
        else:
            d['created_at'] = datetime.fromtimestamp(created_ms / 1000, timezone.utc)
            d[['timestamp']] = d['created_at']


        return d
