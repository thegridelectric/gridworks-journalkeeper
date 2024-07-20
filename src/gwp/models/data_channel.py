"""
The DataChannelSql ORM object should be made via associated pydantic
class DataChannelGt, which includes class validators, using the as_sql method
e.g. ch = DataChannelGt(...).as_sql()
"""

import logging

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship

from gwp.models.message import Base


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

    # Define the relationship to the ReadingSql table
    readings = relationship("ReadingSql", back_populates="data_channel")
