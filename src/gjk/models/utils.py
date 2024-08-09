from typing import List

from sqlalchemy import inspect, tuple_
from sqlalchemy.exc import NoSuchTableError, SQLAlchemyError
from sqlalchemy.orm import Session


def bulk_insert_idempotent(session: Session, orm_object_list: List):
    """
    Idempotently bulk inserts SQLAlchemy objects into the database, inserting only those whose
    primary keys do not already exist.

    Args:
        session (Session): An active SQLAlchemy session used for database operations.
        data_channels (List[object]): A list of SQLAlchemy objects to be conditionally
        inserted into the database.

    Returns:
        None
    """
    if not orm_object_list:
        return

    try:
        # Extract the primary key names
        pk_keys = inspect(orm_object_list[0]).mapper.primary_key

        # Build a query to check for existing primary keys
        pk_tuples = [
            tuple(getattr(obj, key.name) for key in pk_keys) for obj in orm_object_list
        ]

        # Build the filter condition & query existing primary keys, convert
        # to a set for faster lookup
        condition = tuple_(*pk_keys).in_(pk_tuples)
        existing_pks = session.query(*pk_keys).filter(condition).all()
        existing_pks_set = {pk for pk in existing_pks}

        # Filter out objects that already have primary keys in the database
        new_objects = [
            obj
            for obj in orm_object_list
            if tuple(getattr(obj, key.name) for key in pk_keys) not in existing_pks_set
        ]
        session.bulk_save_objects(new_objects)
        session.commit()
    except NoSuchTableError as e:
        print(f"Error: The table does not exist. {e}")
        session.rollback()
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        session.rollback()
