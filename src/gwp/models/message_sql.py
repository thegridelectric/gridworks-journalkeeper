from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base


# Defining the sqlalchemy table format

# Define the base class
Base = declarative_base()


# Define the ORM class
class MessageSql(Base):
    __tablename__ = "messages"
    message_id = Column(String, primary_key=True)
    from_alias = Column(String, nullable=False)
    type_name = Column(String, nullable=False)
    message_persisted_ms = Column(BigInteger, nullable=False)
    payload = Column(JSONB, nullable=False)
    message_created_ms = Column(BigInteger)
