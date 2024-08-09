from gw.utils import snake_to_pascal
from pydantic import BaseModel, field_validator

from gjk.models import ReadingSql
from gjk.type_helpers.utils import (
    check_is_reasonable_unix_time_ms,
    check_is_uuid_canonical_textual,
)


class Reading(BaseModel):
    id: str
    value: int
    time_ms: int
    data_channel_id: str
    message_id: str

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("id")
    @classmethod
    def _check_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"id failed UuidCanonicalTextual format validation: {e}"
            ) from e
        return v

    @field_validator("data_channel_id")
    @classmethod
    def _check_data_channel_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"data_channel_id failed UuidCanonicalTextual format validation: {e}",
            ) from e
        return v

    @field_validator("message_id")
    @classmethod
    def _check_message_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"message_id failed UuidCanonicalTextual format validation: {e}",
            ) from e
        return v

    @field_validator("time_ms")
    @classmethod
    def _check_time_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"time_ms failed ReasonableUnixTimeMs format validation: {e}",
            ) from e
        return v

    def as_sql(self) -> ReadingSql:
        return ReadingSql(**self.model_dump())
