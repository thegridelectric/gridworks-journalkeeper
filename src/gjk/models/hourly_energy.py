"""
The HourlyEnergySql ORM object should be made via associated pydantic
class HourlyEnergyGt, which includes class validators, using the as_sql method
e.g. ch = HourlyEnergyGt(...).as_sql()
"""

from gjk.models.message import Base
from sqlalchemy import Column, BigInteger, Integer, String
from sqlalchemy import UniqueConstraint
from sqlalchemy import tuple_
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict
import pendulum


class HourlyEnergySql(Base):
    """
    Energy consumption of a device specified in power_channel 
    over the hour starting at hour_start_s
    """
    __tablename__ = 'hourly_device_energy'

    id = Column(String, primary_key=True)
    hour_start_s = Column(BigInteger)
    power_channel = Column(String)
    watt_hours = Column(Integer)
    g_node_alias = Column(String)

    # Rows must have a unique combination of start time, channel name, and GNode alias
    __table_args__ = (
        UniqueConstraint('hour_start_s', 'power_channel', 'g_node_alias', name='unique_time_channel_gnode'),
    )


def bulk_insert_hourly_energy(session: Session, hourly_energy_list: List[HourlyEnergySql]):
    """
    Idempotently bulk inserts HourlyEnergySql into the journaldb hourly_device_energy table,
    inserting only those whose primary keys do not already exist AND that don't violate the 
    hour_start_s, power_channel, g_node_alias uniqueness constraint.

    Args:
        session (Session): An active SQLAlchemy session used for database operations.
        hourly_energy_list (List[HourlyEnergySql]): A list of HourlyEnergySql objects to be 
        conditionally inserted into the hourly_device_energy table of the journaldb database

    Returns:
        None
    """
    if not all(isinstance(obj, HourlyEnergySql) for obj in hourly_energy_list):
        raise ValueError("All objects in hourly_energy_list must be HourlyEnergySql objects")

    batch_size = 1000

    for i in range(0, len(hourly_energy_list), batch_size):
        try:
            batch = hourly_energy_list[i:i+batch_size]
            pk_column = HourlyEnergySql.id
            unique_columns = [
                HourlyEnergySql.hour_start_s,
                HourlyEnergySql.power_channel,
                HourlyEnergySql.g_node_alias,
            ]

            pk_set = set()
            unique_set = set()

            for hourly_energy in batch:
                pk_set.add(getattr(hourly_energy, "id"))
                unique_set.add(tuple(getattr(hourly_energy, col.name) for col in unique_columns))

            existing_pks = set(session.query(pk_column).filter(pk_column.in_(pk_set)).all())

            existing_uniques = set(
                session.query(*unique_columns)
                .filter(tuple_(*unique_columns).in_(unique_set))
                .all()
            )

            new_hourly_energy = [
                hourly_energy
                for hourly_energy in batch
                if getattr(hourly_energy, "id") not in existing_pks
                and tuple(getattr(hourly_energy, col.name) for col in unique_columns)
                not in existing_uniques
            ]
            print(f"[{pendulum.from_timestamp(batch[0].hour_start_s)}] Inserting {len(new_hourly_energy)} out of {len(batch)}")
            
            session.bulk_save_objects(new_hourly_energy)
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
