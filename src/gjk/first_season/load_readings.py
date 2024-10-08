import json

import dotenv
import pendulum
from gjk.config import Settings
from gjk.models import MessageSql
from gjk.old_types import BatchedReadings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

import time

timezone = "America/New_York"
start_feb = pendulum.datetime(2024, 2, 1, 0, 0, tz=timezone)
end_feb = pendulum.datetime(2024, 3, 1, 0, 0, tz=timezone)

# Convert to Unix timestamp in milliseconds
start_feb_ms = int(start_feb.timestamp() * 1000)
# end_feb_ms = int(end_feb.timestamp() * 1000)
end_feb_ms = start_feb_ms + 3600 * 1000

# Query
results = (
    session.query(MessageSql)
    .filter(
        MessageSql.from_alias.contains("beech"),
        MessageSql.message_type_name.contains("batched"),
        MessageSql.message_created_ms >= start_feb_ms,
        MessageSql.message_created_ms < end_feb_ms,
    )
    .all()
)

msg = results[0]

br = BatchedReadings.model_validate(msg.payload)
file_name = f"{br.from_g_node_alias}-{br.type_name}-{int(time.time() * 1000)}.json"

file = f"tests/sample_messages/{file_name}"

with open(file, "w") as f:
    json.dump(br.model_dump(exclude_none=True), f, indent=4)
