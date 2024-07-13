from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

# Define the base class
Base = declarative_base()

class MessageSql(Base):
    __tablename__ = "messages"
    message_id = Column(String, primary_key=True)
    from_alias = Column(String, nullable=False)
    type_name = Column(String, nullable=False)
    message_persisted_ms = Column(BigInteger, nullable=False)
    payload = Column(JSONB, nullable=False)
    message_created_ms = Column(BigInteger)
