"""
The MessageSql ORM object should be made via associated pydantic
class Message, which includes class validators, using the as_sql method
e.g. msg = Message(...).as_sql()
"""

import logging
from typing import Dict
from typing import Optional

import pendulum
from pydantic import BaseModel
from pydantic import field_validator
from pydantic.alias_generators import to_pascal
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

from gwp.models.utils import check_is_left_right_dot
from gwp.models.utils import check_is_reasonable_unix_time_ms
from gwp.models.utils import check_is_uuid_canonical_textual


# Define the base class
Base = declarative_base()

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class MessageSql(Base):
    __tablename__ = "messages"
    message_id = Column(String, primary_key=True)
    from_alias = Column(String, nullable=False)
    type_name = Column(String, nullable=False)
    message_persisted_ms = Column(BigInteger, nullable=False)
    payload = Column(JSONB, nullable=False)
    message_created_ms = Column(BigInteger)


class Message(BaseModel):
    message_id: str
    from_alias: str
    type_name: str
    message_persisted_ms: int
    payload: Dict
    message_created_ms: Optional[int] = None

    class Config:
        populate_by_name = True
        alias_generator = to_pascal

    @field_validator("message_id")
    def _check_message_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"message_id failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @field_validator("from_alias")
    def _check_from_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"from_alias failed CheckIsLeftRightDot format validation: {e}"
            )
        return v

    @field_validator("type_name")
    def _check_type_name(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"type_name failed CheckIsLeftRightDot format validation: {e}"
            )
        return v

    @field_validator("message_persisted_ms")
    def _check_message_persisted_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"message_persisted_ms failed ReasonableUnixTimeMs format validation: {e}"
            )
        return v

    @field_validator("message_created_ms")
    def _check_message_created_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"message_created_ms failed ReasonableUnixTimeMs format validation: {e}"
            )
        return v

    def as_sql(self) -> MessageSql:
        return MessageSql(**self.model_dump())
