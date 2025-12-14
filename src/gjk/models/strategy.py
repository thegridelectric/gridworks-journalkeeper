from typing import List

from sqlalchemy import (
    Column,
    String,
)
from sqlalchemy.exc import NoSuchTableError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from gjk.models.message import Base


class StrategySql(Base):
    __tablename__ = "strategies"
    name = Column(String, primary_key=True)
    description = Column(String, nullable=False)

    def to_dict(self):
        d = {
            "Name": self.name,
            "Description": self.description,
        }
        return d

    def __repr__(self):
        return f"<ParamSql({self.id})>"

    def __str__(self):
        return f"<ParamSql({self.id})>"


def bulk_insert_params(db: Session, params_list: List[StrategySql]):
    """
    Idempotently bulk inserts ParamsSql into the journaldb params table

    Args:
        db (Session): An active SQLAlchemy session used for database operations.
        reading_list (List[ParamSql]): A list of ParamSql objects to be conditionally
        inserted into the messages table of the journaldb database

    Returns:
        None
    """
    if not all(isinstance(obj, StrategySql) for obj in params_list):
        raise ValueError("All objects in reading_list must be ParamSql objects")

    batch_size = 1000

    for i in range(0, len(params_list), batch_size):
        try:
            batch = params_list[i : i + batch_size]
            pk_column = StrategySql.name

            pk_set = set()
            for reading in batch:
                pk_set.add(reading.id)

            existing_pks = {
                row[0]
                for row in db.query(pk_column).filter(pk_column.in_(pk_set)).all()
            }

            new_strategies = [
                strategy for strategy in batch if strategy.name not in existing_pks
            ]
            print(f"Inserting {len(new_strategies)} out of {len(batch)}")

            db.bulk_save_objects(new_strategies)
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
