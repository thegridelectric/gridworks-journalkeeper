import logging

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from gjk.models.message import Base

# Define the base class


LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


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
