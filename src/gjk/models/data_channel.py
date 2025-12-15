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


def bulk_insert_datachannels(db: Session, channels: List[DataChannelSql]):
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
