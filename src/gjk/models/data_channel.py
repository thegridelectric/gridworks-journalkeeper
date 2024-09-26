from typing import List

from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint, tuple_
from sqlalchemy.exc import NoSuchTableError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, relationship

from gjk.models.message import Base


class DataChannelSql(Base):
    """
    Data Channel.

    A data channel is a concept of some collection of readings that share all characteristics
    other than time.
    """

    __tablename__ = "data_channels"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    about_node_name = Column(String, nullable=False)
    captured_by_node_name = Column(String, nullable=False)
    telemetry_name = Column(String, nullable=False)
    start_s = Column(Integer)
    in_power_metering = Column(Boolean)
    terminal_asset_alias = Column(String, nullable=False)

    __table_args__ = (
        # name is unique per terminal asset alias
        UniqueConstraint(
            "terminal_asset_alias",
            "name",
            name="unique_name_terminal_asset",
        ),
        # (about_node_name, captured_by_node_name, telemetry_name) is unique per terminal asset alias
        UniqueConstraint(
            "terminal_asset_alias",
            "about_node_name",
            "captured_by_node_name",
            "telemetry_name",
            name="unique_triple_per_ta",
        ),
    )

    # Define the one-to-many relationships with other objects
    readings = relationship("ReadingSql", back_populates="data_channel")
    nodal_hourly_energies = relationship(
        "NodalHourlyEnergySql", back_populates="power_channel"
    )

    def to_dict(self):
        d = {
            "Id": self.id,
            "Name": self.name,
            "DisplayName": self.display_name,
            "AboutNodeName": self.about_node_name,
            "CapturedByNodeName": self.captured_by_node_name,
            "TelemetryName": self.telemetry_name,
            "TerminalAssetAlias": self.terminal_asset_alias,
        }
        if self.start_s:
            d["StartS"] = self.start_s
        if self.in_power_metering:
            d["InPowerMetering"] = self.in_power_metering
        return d

    def __repr__(self):
        ta_short = self.terminal_asset_alias.split(".")[-2]
        power_metering_status = (
            "IN POWER METERING: \n" if self.in_power_metering else ""
        )
        return (
            f"{power_metering_status}"
            f"<DataChannelSql(name='{self.name}', "
            f"about_node_name='{self.about_node_name}', captured_by_node_name='{self.captured_by_node_name}', "
            f"telemetry_name='{self.telemetry_name}', terminal asset: {ta_short}>"
        )

    def __str__(self):
        ta_short = self.terminal_asset_alias.split(".")[-2]
        power_metering_status = (
            "IN POWER METERING: \n" if self.in_power_metering else ""
        )
        return (
            f"{power_metering_status}"
            f"DataChannel(name:{self.name},"
            f"about_node_name: {self.about_node_name}, captured_by_node_name: {self.captured_by_node_name}, "
            f"telemetry_name: {self.telemetry_name}, terminal asset: {ta_short}"
        )


def bulk_insert_datachannels(session: Session, datachannel_list: List[DataChannelSql]):
    """
    Idempotently bulk inserts DataChannelSql into the journaldb messages table,
    inserting only those whose primary keys do not already exist AND that
    don't violate the uniqueness constraint.

    Args:
        session (Session): An active SQLAlchemy session used for database operations.
        datachannel_list (List[DataChannelSql]): A list of DataChannelSql objects to be conditionally
        inserted into the data_channels table of the journaldb database

    Returns:
        None
    """
    if not all(isinstance(obj, DataChannelSql) for obj in datachannel_list):
        raise ValueError(
            "All objects in datachannel_list must be DataChannelSql objects"
        )

    batch_size = 10

    for i in range(0, len(datachannel_list), batch_size):
        try:
            batch = datachannel_list[i : i + batch_size]
            pk_column = DataChannelSql.id
            unique_columns = [
                DataChannelSql.name,
                DataChannelSql.terminal_asset_alias,
                DataChannelSql.about_node_name,
                DataChannelSql.captured_by_node_name,
                DataChannelSql.telemetry_name,
            ]

            pk_set = set()
            unique_set = set()

            for datachannel in batch:
                pk_set.add(datachannel.id)
                unique_set.add(
                    tuple(getattr(datachannel, col.name) for col in unique_columns)
                )

            existing_pks = set(
                session.query(pk_column).filter(pk_column.in_(pk_set)).all()
            )

            existing_uniques = set(
                session.query(*unique_columns)
                .filter(tuple_(*unique_columns).in_(unique_set))
                .all()
            )

            new_datachannels = [
                datachannel
                for datachannel in batch
                if datachannel.id not in existing_pks
                and tuple(getattr(datachannel, col.name) for col in unique_columns)
                not in existing_uniques
            ]
            print(f"Inserting {len(new_datachannels)} out of {len(batch)}")

            session.bulk_save_objects(new_datachannels)
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
