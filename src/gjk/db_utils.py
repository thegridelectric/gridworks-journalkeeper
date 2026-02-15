from typing import List
from sqlalchemy import inspect, tuple_
from sqlalchemy.exc import NoSuchTableError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from gw_data.db.models import (
    DataChannelSql,
    MessageSql
)


def bulk_insert_idempotent(session: Session, orm_object_list: list):
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

def insert_single_message(db: Session, msg: MessageSql) -> bool:
    try:
        db.add(msg)
        db.commit()
        return True
    except Exception:
        return False


def bulk_insert_messages(db: Session, message_list: list[MessageSql]):
    """
    Idempotently bulk inserts MessageSql into the journaldb messages table,
    inserting only those whose primary keys do not already exist.

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
        pk_column = MessageSql.id

        pk_set = set()

        for message in message_list:
            pk_set.add(message.id)

        existing_pks = {
            row[0] for row in db.query(pk_column).filter(pk_column.in_(pk_set)).all()
        }

        new_messages = [
            msg
            for msg in message_list
            if msg.id not in existing_pks
        ]
        print(f"Inserting {len(new_messages)} out of {len(message_list)}")
        db.bulk_save_objects(new_messages)
        db.commit()

    except NoSuchTableError as e:
        print(f"Error: The table does not exist. {e}")
        db.rollback()
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        db.rollback()

def bulk_insert_datachannels(db: Session, channels: list[DataChannelSql]):
    """
    Idempotently bulk inserts DataChannelSql into the journaldb messages table,
    inserting only those whose primary keys do not already exist AND that
    don't violate the two other uniqueness constraint.

    Args:
        db(Session): An active SQLAlchemy session used for database operations.
        datachannel_list (List[DataChannelSql]): A list of DataChannelSql objects to be conditionally
        inserted into the data_channels table of the journaldb database

    Returns:
        None
    """
    if not all(isinstance(obj, DataChannelSql) for obj in channels):
        raise ValueError(
            "All objects in datachannel_list must be DataChannelSql objects"
        )

    batch_size = 100

    for i in range(0, len(channels), batch_size):
        try:
            batch = channels[i : i + batch_size]
            pk_column = DataChannelSql.id
            uniq_1_columns = [DataChannelSql.terminal_asset_alias, DataChannelSql.name]
            uniq_2_columns = [
                DataChannelSql.terminal_asset_alias,
                DataChannelSql.about_node_name,
                DataChannelSql.captured_by_node_name,
                DataChannelSql.telemetry_name,
            ]

            pk_set = {ch.id for ch in channels}
            uniq_1_set = {
                tuple(getattr(ch, col.name) for col in uniq_1_columns)
                for ch in channels
            }
            uniq_2_set = {
                tuple(getattr(ch, col.name) for col in uniq_2_columns)
                for ch in channels
            }

            existing_pks = {
                row[0]
                for row in db.query(pk_column).filter(pk_column.in_(pk_set)).all()
            }
            existing_uniq_1 = set(
                db.query(*uniq_1_columns)
                .filter(tuple_(*uniq_1_columns).in_(uniq_1_set))
                .all()
            )
            existing_uniq_2 = set(
                db.query(*uniq_2_columns)
                .filter(tuple_(*uniq_2_columns).in_(uniq_2_set))
                .all()
            )

            new = [
                ch
                for ch in channels
                if ch.id not in existing_pks
                and tuple(getattr(ch, col.name) for col in uniq_1_columns)
                not in existing_uniq_1
                and tuple(getattr(ch, col.name) for col in uniq_2_columns)
                not in existing_uniq_2
            ]
            print(f"Inserting {len(new)} out of {len(batch)}")

            db.bulk_save_objects(new)
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
