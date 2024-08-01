"""
The ReadingSql ORM object should be made via associated pydantic
class Reading, which includes class validators, using the as_sql method
e.g. reading = Reading(...).as_sql()
"""

import logging
from typing import List

from gw.utils import snake_to_pascal
from pydantic import BaseModel
from pydantic import field_validator
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import tuple_
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship

from gjk.first_season.utils import str_from_ms
from gjk.models.message import Base
from gjk.models.utils import check_is_reasonable_unix_time_ms
from gjk.models.utils import check_is_uuid_canonical_textual


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


def bulk_insert_readings(session: Session, reading_list: List[ReadingSql]):
    """
    Idempotently bulk inserts ReadingSql into the journaldb messages table,
    inserting only those whose primary keys do not already exist AND that
    don't violate the from_alias, type_name, message_persisted_ms uniqueness
    constraint.

    Args:
        session (Session): An active SQLAlchemy session used for database operations.
        reading_list (List[ReadingSql]): A list of ReadingSql objects to be conditionally
        inserted into the messages table of the journaldb database

    Returns:
        None
    """
    if not all(isinstance(obj, ReadingSql) for obj in reading_list):
        raise ValueError("All objects in reading_list must be ReadingSql objects")

    batch_size = 1000

    for i in range(0, len(reading_list), batch_size):
        try:
            batch = reading_list[i:i+batch_size]
            pk_column = ReadingSql.id
            unique_columns = [
                ReadingSql.time_ms,
                ReadingSql.data_channel_id,
                ReadingSql.message_id,
            ]

            pk_set = set()
            unique_set = set()

            for reading in batch:
                pk_set.add(getattr(reading, "id"))
                unique_set.add(tuple(getattr(reading, col.name) for col in unique_columns))

            existing_pks = set(session.query(pk_column).filter(pk_column.in_(pk_set)).all())

            existing_uniques = set(
                session.query(*unique_columns)
                .filter(tuple_(*unique_columns).in_(unique_set))
                .all()
            )

            new_readings = [
                reading
                for reading in batch
                if getattr(reading, "id") not in existing_pks
                and tuple(getattr(reading, col.name) for col in unique_columns)
                not in existing_uniques
            ]
            print(f"[{str_from_ms(batch[0].time_ms)}] Inserting {len(new_readings)} out of {len(batch)}")
            
            session.bulk_save_objects(new_readings)
            session.commit()

        except NoSuchTableError as e:
            print(f"Error: The table does not exist. {e}")
            session.rollback()
        except OperationalError as e:
            print(f"Operational Error! {e}")
            session.rollback()
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            session.rollback()
    