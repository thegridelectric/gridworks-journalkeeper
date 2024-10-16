from typing import List

import pendulum
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    tuple_,
)
from sqlalchemy.exc import NoSuchTableError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, relationship

from gjk.models.message import Base

# Define the base class


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
        # Index on message_id to speed up message-based queries
        Index("ix_message_id", "message_id"),
        # Composite index on data_channel_id and time_ms to speed up time-based queries for a channel
        Index("ix_data_channel_time", "data_channel_id", "time_ms"),
    )

    data_channel = relationship("DataChannelSql", back_populates="readings")

    def to_dict(self):
        d = {
            "Id": self.id,
            "Value": self.value,
            "TimeMs": self.time_ms,
            "DataChannelId": self.data_channel_id,
            "MessageId": self.message_id,
        }
        return d

    def __repr__(self):
        return f"<ReadingSql({self.data_channel.name}: {self.value} {self.data_channel.telemetry_name}', time={pendulum.from_timestamp(self.time_ms / 1000)})>"

    def __str__(self):
        return f"{self.data_channel.name}: {self.value} {self.data_channel.telemetry_name}', time={pendulum.from_timestamp(self.time_ms / 1000)}>"


def bulk_insert_readings(db: Session, reading_list: List[ReadingSql]):
    """
    Idempotently bulk inserts ReadingSql into the journaldb messages table,
    inserting only those whose primary keys do not already exist AND that
    don't violate the from_alias, type_name, message_persisted_ms uniqueness
    constraint.

    Args:
        db (Session): An active SQLAlchemy session used for database operations.
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

            existing_pks = {
                row[0]
                for row in db.query(pk_column).filter(pk_column.in_(pk_set)).all()
            }

            existing_uniques = set(
                db.query(*unique_columns)
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
            print(f"Inserting {len(new_readings)} out of {len(batch)}")

            db.bulk_save_objects(new_readings)
            db.commit()

        except NoSuchTableError as e:
            print(f"Error: The table does not exist. {e}")
            db.rollback()
        except OperationalError as e:
            print(f"Operational Error! {e}")
            db.rollback()
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            db.rollback()
