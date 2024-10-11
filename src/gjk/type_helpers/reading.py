import uuid
from typing import Any, Dict

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from gjk.named_types.data_channel_gt import DataChannelGt
from gjk.property_format import (
    UTCMilliseconds,
    UUID4Str,
)


class Reading(BaseModel):
    id: UUID4Str = Field(default_factory=lambda: str(uuid.uuid4()))
    value: int
    time_ms: UTCMilliseconds
    data_channel: DataChannelGt
    message_id: UUID4Str

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=snake_to_pascal,
    )

    @classmethod
    def from_dict(cls, d: dict) -> "Reading":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    def to_dict(self) -> Dict[str, Any]:
        """
        Handles lists of enums differently than model_dump
        """
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["DataChannel"] = self.data_channel.to_dict()
        return d

    def to_sql_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["data_channel"] = self.data_channel.to_dict()
        d.pop("type_name", None)
        d.pop("version", None)
        return d
