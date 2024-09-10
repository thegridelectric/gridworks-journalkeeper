from typing import Any, Dict, Optional

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError

from gjk.type_helpers.property_format import (
    LeftRightDotStr,
    ReasonableUnixTimeMs,
    UUID4Str,
)


class Message(BaseModel):
    message_id: UUID4Str
    from_alias: LeftRightDotStr
    message_type_name: LeftRightDotStr
    message_persisted_ms: ReasonableUnixTimeMs
    payload: Dict
    message_created_ms: Optional[ReasonableUnixTimeMs] = None

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

    def to_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        return d

    def to_sql_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        return d
