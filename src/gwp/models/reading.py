"""
The ReadingSql ORM object should be made via associated pydantic
class Reading, which includes class validators, using the as_sql method
e.g. reading = Reading(...).as_sql()
"""

import logging
from gw.utils import snake_to_pascal
from pydantic import BaseModel
from pydantic import field_validator
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from gwp.models.utils import check_is_reasonable_unix_time_ms
from gwp.models.utils import check_is_uuid_canonical_textual

from gwp.models.message import Base
# Define the base class


LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class ReadingSql(Base):
    __tablename__ = "readings"
    id = Column(String, primary_key=True)
    value = Column(BigInteger, nullable=False)
    time_ms = Column(BigInteger, nullable=False)
    data_channel_id = Column(String, ForeignKey('data_channels.id'), nullable=False)
    message_id = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('time_ms', 'data_channel_id', 'message_id', name='unique_time_data_channel_message'),
    )

    data_channel = relationship("DataChannelSql", back_populates="readings")


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
    def _check_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"id failed UuidCanonicalTextual format validation: {e}"
            )
        return v
    
    @field_validator("data_channel_id")
    def _check_data_channel_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"data_channel_id failed UuidCanonicalTextual format validation: {e}"
            )
        return v
    
    @field_validator("message_id")
    def _check_message_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"message_id failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @field_validator("time_ms")
    def _check_time_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"time_ms failed ReasonableUnixTimeMs format validation: {e}"
            )
        return v

    def as_sql(self) -> ReadingSql:
        return ReadingSql(**self.model_dump())
