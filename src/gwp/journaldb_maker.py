import json
import uuid
from typing import List

from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from gwp.models import MessageSql
from gwp.types import Message


file_name = "hw1.isone.me.versant.keene.beech.scada-power.watts-1715904078460-100.26.91.172.json"
msg_file = f"tests/sample_messages/{file_name}"

from_alias = file_name.split("-")[0]
type_name = file_name.split("-")[1]
message_persisted_ms = int(file_name.split("-")[2])

with open(msg_file, "r") as file:
    content = json.load(file)

payload = content.get("Payload", {})
message_id = content.get("Header", {}).get("MessageId", None)
message_created_ms = content.get("Header", {}).get("MessageCreatedMs", None)

# Generate a new UUID if message_id is None or blank
if not message_id:
    message_id = str(uuid.uuid4())

if message_created_ms:
    message_created_ms = int(message_created_ms)
else:
    message_created_ms = None


# Create an instance of GwMessagePydantic
msg = Message(
    from_alias=from_alias,
    type_name=type_name,
    message_persisted_ms=message_persisted_ms,
    payload=payload,
    message_id=message_id,
    message_created_ms=message_created_ms,
)

messages = [msg]


# Database credentials
DATABASE_URI = "postgresql://persister:star5fish@journaldb.electricity.works/journaldb"

# Create an engine and session
engine = create_engine(DATABASE_URI)
inspector = inspect(engine)

for table in [MessageSql]:
    if table.__tablename__ not in inspector.get_table_names():
        table.__table__.create(engine)
    else:
        print(f"Table '{table.__tablename__ }' already exists.")


def add_messages(messages: List[Message]):
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # Bulk insert messages
        session.bulk_insert_mappings(MessageSql, [msg.model_dump() for msg in messages])
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
