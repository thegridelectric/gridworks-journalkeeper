"""
The MessageSql ORM object should be made via associated pydantic
class Message, which includes class validators, using the as_sql method
e.g. msg = Message(...).as_sql()
"""

import logging
from typing import Dict
from typing import List
from typing import Optional

import pendulum
from gw.utils import snake_to_pascal
from pydantic import BaseModel
from pydantic import field_validator
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import tuple_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base

from gjk.models.utils import check_is_left_right_dot
from gjk.models.utils import check_is_reasonable_unix_time_ms
from gjk.models.utils import check_is_uuid_canonical_textual


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

    __table_args__ = (
        UniqueConstraint(
            "from_alias",
            "type_name",
            "message_persisted_ms",
            name="uq_from_type_message",
        ),
    )


class Message(BaseModel):
    message_id: str
    from_alias: str
    type_name: str
    message_persisted_ms: int
    payload: Dict
    message_created_ms: Optional[int] = None

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

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
        if v:
            try:
                check_is_reasonable_unix_time_ms(v)
            except ValueError as e:
                raise ValueError(
                    f"message_created_ms failed ReasonableUnixTimeMs format validation: {e}"
                )
        return v

    def as_sql(self) -> MessageSql:
        return MessageSql(**self.model_dump())


def bulk_insert_messages(session: Session, message_list: List[MessageSql]):
    """
    Idempotently bulk inserts MessageSql into the journaldb messages table,
    inserting only those whose primary keys do not already exist AND that
    don't violate the from_alias, type_name, message_persisted_ms uniqueness
    constraint.

    Args:
        session (Session): An active SQLAlchemy session used for database operations.
        message_list (List[MessageSql]): A list of MessageSql objects to be conditionally
        inserted into the messages table of the journaldb database

    Returns:
        None
    """
    if not all(isinstance(obj, MessageSql) for obj in message_list):
        raise ValueError("All objects in message_list must be MessageSql objects")

    try:
        pk_column = MessageSql.message_id
        unique_columns = [
            MessageSql.from_alias,
            MessageSql.type_name,
            MessageSql.message_persisted_ms,
        ]

        pk_set = set()
        unique_set = set()

        for message in message_list:
            pk_set.add(getattr(message, "message_id"))
            unique_set.add(tuple(getattr(message, col.name) for col in unique_columns))

        existing_pks = set(session.query(pk_column).filter(pk_column.in_(pk_set)).all())

        existing_uniques = set(
            session.query(*unique_columns)
            .filter(tuple_(*unique_columns).in_(unique_set))
            .all()
        )

        new_messages = [
            msg
            for msg in message_list
            if getattr(msg, "message_id") not in existing_pks
            and tuple(getattr(msg, col.name) for col in unique_columns)
            not in existing_uniques
        ]

        session.bulk_save_objects(new_messages)
        session.commit()

    except NoSuchTableError as e:
        print(f"Error: The table does not exist. {e}")
        session.rollback()
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        session.rollback()
