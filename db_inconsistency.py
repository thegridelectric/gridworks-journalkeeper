import dotenv
import pendulum
from gjk.config import Settings
from gjk.models import DataChannelSql, MessageSql
from gjk.types import BatchedReadings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from gjk.codec import from_dict, pyd_to_sql
from gjk.first_season.beech_channels import data_channels_match_db, BEECH_CHANNELS_BY_NAME
from gjk.models.message import bulk_insert_messages

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

first_id = '55faec9b-7ce6-4a64-9d5d-e07e20cf6e15'
later_id = 'a1aa5751-74cc-4e6a-863d-7ffcf3de6ade'

first_msg = session.query(MessageSql).filter(MessageSql.message_id == first_id).first()
later_msg = session.query(MessageSql).filter(MessageSql.message_id == later_id).first()

# For each data channel in the first message
dc_list = first_msg.payload['DataChannelList']

for dc in dc_list:

    # Find the key in the local channels that corresponds to the data channel ID
    for key, value in BEECH_CHANNELS_BY_NAME.items():
        if value.id == dc['Id']:
            name = key
    
    dc['TerminalAssetAlias'] = BEECH_CHANNELS_BY_NAME[name].terminal_asset_alias
    dc['Version'] = BEECH_CHANNELS_BY_NAME[name].version
    dc['CapturedByNodeName'] = BEECH_CHANNELS_BY_NAME[name].captured_by_node_name
    dc['DisplayName'] = dc['DisplayName'].lower()

# Update the payload with the updated Data Channel list
first_msg.payload['DataChannelList'] = dc_list

# Check it matches local db
first_br: BatchedReadings = from_dict(first_msg.payload)
later_br: BatchedReadings = from_dict(later_msg.payload)
dc_list = [pyd_to_sql(dc) for dc in first_br.data_channel_list]
data_channels_match_db(session, dc_list, check_missing=False)

# Upload to database
bulk_insert_messages(session, [first_msg])
session.commit()

# Check the update
first_msg = session.query(MessageSql).filter(MessageSql.message_id == first_id).first()
print(first_msg.payload['DataChannelList'] == dc_list)