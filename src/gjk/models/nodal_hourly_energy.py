"""
The NodalHourlyEnergySql ORM object should be made via associated pydantic
class HourlyEnergyGt, which includes class validators, using the as_sql method
e.g. ch = HourlyEnergyGt(...).as_sql()
"""

from typing import List

import pendulum
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    tuple_,
)
from sqlalchemy.exc import NoSuchTableError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, relationship

from gjk.models.message import Base


class NodalHourlyEnergySql(Base):
    """
    Energy consumption of a device specified in power_channel
    over the hour starting at hour_start_s
    """

    __tablename__ = "nodal_hourly_energy"

    id = Column(String, primary_key=True)
    hour_start_s = Column(BigInteger)  # TODO: nullable = False
    power_channel_id = Column(String, ForeignKey("data_channels.id"), nullable=False)
    watt_hours = Column(Integer)  # TODO: nullable = False

    # Rows must have a unique combination of start time and channel name
    __table_args__ = (
        UniqueConstraint(
            "hour_start_s",
            "power_channel_id",
            name="unique_time_channel",
        ),
    )

    power_channel = relationship(
        "DataChannelSql", back_populates="nodal_hourly_energies"
    )

    def to_dict(self):
        d = {
            "Id": self.id,
            "PowerChannel": self.power_channel.to_dict(),
            "HourStartS": self.hour_start_s,
            "WattHours": self.watt_hours,
        }
        return d

    def __repr__(self):
        hs = pendulum.from_timestamp(self.hour_start_s, tz="America/New_York")
        return (
            f"<[{self.power_channel.name}] {hs.format('MMM DD, HH:mm')}: (Hour Starting)"
            f"{self.watt_hours / 1000} kWh>"
        )

    def __str__(self):
        hs = pendulum.from_timestamp(self.hour_start_s, tz="America/New_York")
        return (
            f"[{self.power_channel.name}] {hs.format('MMM DD, HH:mm')}: (Hour Starting)"
            f"{self.watt_hours / 1000} kWh"
        )


def bulk_insert_nodal_hourly_energy(
    session: Session, hourly_energy_list: List[NodalHourlyEnergySql]
):
    """
    Idempotently bulk inserts NodalHourlyEnergySql into the journaldb hourly_device_energy table,
    inserting only those whose primary keys do not already exist AND that don't violate the
    hour_start_s, power_channel, g_node_alias uniqueness constraint.

    Args:
        session (Session): An active SQLAlchemy session used for database operations.
        hourly_energy_list (List[NodalHourlyEnergySql]): A list of NodalHourlyEnergySql objects to be
        conditionally inserted into the hourly_device_energy table of the journaldb database

    Returns:
        None
    """
    if not all(isinstance(obj, NodalHourlyEnergySql) for obj in hourly_energy_list):
        raise ValueError(
            "All objects in hourly_energy_list must be NodalHourlyEnergySql objects"
        )

    batch_size = 1000

    for i in range(0, len(hourly_energy_list), batch_size):
        try:
            batch = hourly_energy_list[i : i + batch_size]
            pk_column = NodalHourlyEnergySql.id
            unique_columns = [
                NodalHourlyEnergySql.hour_start_s,
                NodalHourlyEnergySql.power_channel_id,
            ]

            pk_set = set()
            unique_set = set()

            for hourly_energy in batch:
                pk_set.add(hourly_energy.id)
                unique_set.add(
                    tuple(getattr(hourly_energy, col.name) for col in unique_columns)
                )

            existing_pks = set(
                session.query(pk_column).filter(pk_column.in_(pk_set)).all()
            )

            existing_uniques = set(
                session.query(*unique_columns)
                .filter(tuple_(*unique_columns).in_(unique_set))
                .all()
            )

            new_hourly_energy = [
                hourly_energy
                for hourly_energy in batch
                if hourly_energy.id not in existing_pks
                and tuple(getattr(hourly_energy, col.name) for col in unique_columns)
                not in existing_uniques
            ]
            print(
                f"[{pendulum.from_timestamp(batch[0].hour_start_s)}] Inserting {len(new_hourly_energy)} out of {len(batch)}"
            )

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
