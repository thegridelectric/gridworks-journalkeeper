from typing import List

import pendulum
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
    UniqueConstraint,
    tuple_,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import NoSuchTableError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from gjk.models.message import Base


class ParamSql(Base):
    __tablename__ = "params"
    id = Column(String, primary_key=True)
    strategy = Column(String, ForeignKey("strategy.name"), nullable=False)
    from_alias = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    unix_ms = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "strategy", "from_alias", "unix_ms", name="unique_strategy_gnode_time"
        ),
    )

    def to_dict(self):
        d = {
            "Id": self.id,
            "Strategy": self.strategy,
            "FromAlias": self.from_alias,
            "Payload": self.payload,
            "UnixMs": self.unix_ms,
        }
        return d

    def __repr__(self):
        return f"<ParamSql({self.strategy}, {self.from_alias}, {pendulum.from_timestamp(self.unix_ms / 1000)})>"

    def __str__(self):
        return f"<ParamSql({self.strategy}, {self.from_alias}, {pendulum.from_timestamp(self.unix_ms / 1000)})>"


def bulk_insert_param_values(db: Session, params_list: List[ParamSql]):
    """
    Idempotently bulk inserts ParamsSql into the journaldb params table

    Args:
        db (Session): An active SQLAlchemy session used for database operations.
        reading_list (List[ParamSql]): A list of ParamSql objects to be conditionally
        inserted into the messages table of the journaldb database

    Returns:
        None
    """
    if not all(isinstance(obj, ParamSql) for obj in params_list):
        raise ValueError("All objects in reading_list must be ParamSql objects")

    batch_size = 1000

    for i in range(0, len(params_list), batch_size):
        try:
            batch = params_list[i : i + batch_size]
            pk_column = ParamSql.id
            unique_columns = [
                ParamSql.strategy,
                ParamSql.from_alias,
                ParamSql.unix_ms,
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

            new_params = [
                reading
                for reading in batch
                if reading.id not in existing_pks
                and tuple(getattr(reading, col.name) for col in unique_columns)
                not in existing_uniques
            ]
            print(f"Inserting {len(new_params)} out of {len(batch)}")

            db.bulk_save_objects(new_params)
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
