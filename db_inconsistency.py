import dotenv
from gjk.codec import from_dict, pyd_to_sql
from gjk.config import Settings
from gjk.first_season.beech_channels import (
    BEECH_CHANNELS_BY_NAME,
    data_channels_match_db,
)
from gjk.models import MessageSql
from gjk.types import BatchedReadings
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

first_id = "55faec9b-7ce6-4a64-9d5d-e07e20cf6e15"
later_id = "a1aa5751-74cc-4e6a-863d-7ffcf3de6ade"

first_msg = session.query(MessageSql).filter(MessageSql.message_id == first_id).first()
later_msg = session.query(MessageSql).filter(MessageSql.message_id == later_id).first()

# Edit the datachannel list
dc_list = first_msg.payload["DataChannelList"].copy()
for dc in dc_list:
    for key, value in BEECH_CHANNELS_BY_NAME.items():
        if value.id == dc["Id"]:
            name = key
    dc["TerminalAssetAlias"] = BEECH_CHANNELS_BY_NAME[name].terminal_asset_alias
    dc["Version"] = BEECH_CHANNELS_BY_NAME[name].version
    dc["CapturedByNodeName"] = BEECH_CHANNELS_BY_NAME[name].captured_by_node_name
    dc["DisplayName"] = BEECH_CHANNELS_BY_NAME[name].display_name

# Check it matches local db
first_br: BatchedReadings = from_dict(first_msg.payload)
dc_list_check = [pyd_to_sql(dc) for dc in first_br.data_channel_list]
data_channels_match_db(session, dc_list_check, check_missing=False)

# Save and commit (twice)
try:
    first_msg.payload = {**first_msg.payload, "DataChannelList": dc_list}
    session.commit()
    first_msg.payload = {**first_msg.payload, "DataChannelList": dc_list}
    session.commit()
except SQLAlchemyError as e:
    session.rollback()
    print(f"An error occurred: {e}")

# Check the update
first_msg = session.query(MessageSql).filter(MessageSql.message_id == first_id).first()
if first_msg.payload["DataChannelList"] == dc_list:
    print("\nSuccess! DataChannelList was updated in message payload.\n")
else:
    print("\nDataChannelList was NOT updated in message payload.\n")

session.close()
