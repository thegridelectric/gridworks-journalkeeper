from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    tuple_,
)

from gjk.models.message import Base

class ParamsSql(Base):
    __tablename__ = "params"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    strategy = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "name",
            "strategy"
        )
    )
