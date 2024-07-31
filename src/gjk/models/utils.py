from typing import List

import pendulum
from sqlalchemy import UniqueConstraint
from sqlalchemy import inspect
from sqlalchemy import tuple_
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def bulk_insert_idempotent(session: Session, orm_object_list: List):
    """
    Idempotently bulk inserts SQLAlchemy objects of the same type into the database, 
    inserting only those that would not violate a uniqueness constraint

    Args:
        session (Session): An active SQLAlchemy session used for database operations.
        data_channels (List[object]): A list of SQLAlchemy objects to be conditionally
        inserted into the database.

    Returns:
        None
    """
    if not orm_object_list:
        return
    
    first_type = type(orm_object_list[0])
    if not all(isinstance(obj, first_type) for obj in orm_object_list):
        raise ValueError("All objects in orm_object_list must be of the same type.")

    try:
        # Extract the primary key names
        pk_keys = inspect(orm_object_list[0]).mapper.primary_key
        
        # Extract all unique constraints
        unique_constraints = [
            constraint for constraint in inspect(orm_object_list[0]).mapper.tables[0].constraints
            if isinstance(constraint, UniqueConstraint)
        ]

        # Build a set to store unique values
        unique_values_set = set()

        # Add primary keys to this set
        for obj in orm_object_list:
            pk_values = tuple(getattr(obj, key.name) for key in pk_keys)
            unique_values_set.add(pk_values)

        # Add unique constraints to this set
        for constraint in unique_constraints:
            columns = constraint.columns.keys()
            for obj in orm_object_list:
                unique_values = tuple(getattr(obj, col) for col in columns)
                unique_values_set.add(unique_values)

        # Build a filter condition for primary keys
        pk_condition = tuple_(*pk_keys).in_(unique_values_set)
        existing_pks = session.query(*pk_keys).filter(pk_condition).all()
        existing_pks_set = {pk for pk in existing_pks}
        
        # Filter out objects that already exist by primary keys or unique constraints
        new_objects = []
        for obj in orm_object_list:
            pk_values = tuple(getattr(obj, key.name) for key in pk_keys)
            if pk_values in existing_pks_set:
                continue

            unique_conflict = False
            for constraint in unique_constraints:
                columns = constraint.columns.keys()
                unique_values = tuple(getattr(obj, col) for col in columns)
                if session.query(*columns).filter(
                    tuple_(*columns).in_([unique_values])
                ).first():
                    unique_conflict = True
                    break

            if not unique_conflict:
                new_objects.append(obj)

        session.bulk_save_objects(new_objects)
        session.commit()

    except NoSuchTableError as e:
        print(f"Error: The table does not exist. {e}")
        session.rollback()
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        session.rollback()


def check_is_uuid_canonical_textual(v: str) -> None:
    """Checks UuidCanonicalTextual format

    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not UuidCanonicalTextual format
    """
    try:
        x = v.split("-")
    except AttributeError as e:
        raise ValueError(f"Failed to split on -: {e}")
    if len(x) != 5:
        raise ValueError(f"{v} split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError:
            raise ValueError(f"Words of {v} are not all hex")
    if len(x[0]) != 8:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[1]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[2]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[3]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[4]) != 12:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods, with
    the most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
    """
    from typing import List

    try:
        x: List[str] = v.split(".")
    except:
        raise ValueError(f"Failed to seperate <{v}> into words with split'.'")
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of <{v}> must start with alphabet char."
        )
    for word in x:
        if not word.isalnum():
            raise ValueError(f"words of <{v}> split by by '.' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of <{v}> must be lowercase.")


def check_is_reasonable_unix_time_ms(v: int) -> None:
    """Checks ReasonableUnixTimeMs format

    ReasonableUnixTimeMs format: unix milliseconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeMs format
    """

    if pendulum.parse("2000-01-01T00:00:00Z").int_timestamp * 1000 > v:  # type: ignore[attr-defined]
        raise ValueError(f"<{v}> must be after Jan 1 2000")
    if pendulum.parse("3000-01-01T00:00:00Z").int_timestamp * 1000 < v:  # type: ignore[attr-defined]
        raise ValueError(f"<{v}> must be before Jan 1 3000")


def check_is_reasonable_unix_time_s(v: int) -> None:
    """Checks ReasonableUnixTimeS format

    ReasonableUnixTimeS format: epoch time between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeS format
    """

    if pendulum.parse("2000-01-01T00:00:00Z").int_timestamp > v:  # type: ignore[attr-defined]
        raise ValueError(f"<{v}> must be after Jan 1 2000")
    if pendulum.parse("3000-01-01T00:00:00Z").int_timestamp < v:  # type: ignore[attr-defined]
        raise ValueError(f"<{v}> must be before Jan 1 3000")
