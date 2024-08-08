"""
The ReadingSql ORM object should be made via associated pydantic
class Reading, which includes class validators, using the as_sql method
e.g. reading = Reading(...).as_sql()
"""

import logging
from typing import List

import pendulum
from sqlalchemy import BigInteger, Column, ForeignKey, String, UniqueConstraint, tuple_
from sqlalchemy.exc import NoSuchTableError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, relationship

from gjk.first_season.utils import str_from_ms
from gjk.models.message import Base

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
    data_channel_id = Column(String, ForeignKey("data_channels.id"), nullable=False)
    message_id = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "time_ms",
            "data_channel_id",
            "message_id",
            name="unique_time_data_channel_message",
        ),
    )

    data_channel = relationship("DataChannelSql", back_populates="readings")

    def __repr__(self):
        return f"<ReadingSql({self.data_channel.name}: {self.value} {self.data_channel.telemetry_name}', time={pendulum.from_timestamp(self.time_ms / 1000)})>"

    def __str__(self):
        return f"{self.data_channel.name}: {self.value} {self.data_channel.telemetry_name}', time={pendulum.from_timestamp(self.time_ms / 1000)}>"


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
            batch = reading_list[i : i + batch_size]
            pk_column = ReadingSql.id
            unique_columns = [
                ReadingSql.time_ms,
                ReadingSql.data_channel_id,
                ReadingSql.message_id,
            ]

            pk_set = set()
            unique_set = set()

            for reading in batch:
                pk_set.add(reading.id)
                unique_set.add(
                    tuple(getattr(reading, col.name) for col in unique_columns)
                )

            existing_pks = set(
                session.query(pk_column).filter(pk_column.in_(pk_set)).all()
            )

            existing_uniques = set(
                session.query(*unique_columns)
                .filter(tuple_(*unique_columns).in_(unique_set))
                .all()
            )

            new_readings = [
                reading
                for reading in batch
                if reading.id not in existing_pks
                and tuple(getattr(reading, col.name) for col in unique_columns)
                not in existing_uniques
            ]
            print(
                f"[{str_from_ms(batch[0].time_ms)}] Inserting {len(new_readings)} out of {len(batch)}"
            )

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
