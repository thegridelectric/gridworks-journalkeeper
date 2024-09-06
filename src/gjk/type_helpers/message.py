from typing import Dict, Optional

from gw.utils import snake_to_pascal
from pydantic import BaseModel, ConfigDict, field_validator

from gjk.models import MessageSql
from gjk.type_helpers.utils import (
    check_is_left_right_dot,
    check_is_reasonable_unix_time_ms,
    check_is_uuid_canonical_textual,
)


class Message(BaseModel):
    message_id: str
    from_alias: str
    type_name: str
    message_persisted_ms: int
    payload: Dict
    message_created_ms: Optional[int] = None

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=snake_to_pascal,
    )

    @field_validator("message_id")
    def _check_message_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"message_id failed UuidCanonicalTextual format validation: {e}"
            ) from e
        return v

    @field_validator("from_alias")
    def _check_from_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"from_alias failed CheckIsLeftRightDot format validation: {e}"
            ) from e
        return v

    @field_validator("type_name")
    def _check_type_name(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"type_name failed CheckIsLeftRightDot format validation: {e}"
            ) from e
        return v

    @field_validator("message_persisted_ms")
    def _check_message_persisted_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"message_persisted_ms failed ReasonableUnixTimeMs format validation: {e}"
            ) from e
        return v

    @field_validator("message_created_ms")
    def _check_message_created_ms(cls, v: int) -> int:
        if v:
            try:
                check_is_reasonable_unix_time_ms(v)
            except ValueError as e:
                raise ValueError(
                    f"message_created_ms failed ReasonableUnixTimeMs format validation: {e}"
                ) from e
        return v

    def as_sql(self) -> MessageSql:
        return MessageSql(**self.model_dump())
