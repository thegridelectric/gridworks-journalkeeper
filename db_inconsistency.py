import dotenv
import pendulum
from gjk.config import Settings
from gjk.models import DataChannelSql, MessageSql
from gjk.types import BatchedReadings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from gjk.codec import from_dict, pyd_to_sql
from gjk.first_season.beech_channels import data_channels_match_db

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

first_id = '55faec9b-7ce6-4a64-9d5d-e07e20cf6e15'
later_id = 'a1aa5751-74cc-4e6a-863d-7ffcf3de6ade'

first_msg = session.query(MessageSql).filter(MessageSql.message_id == first_id).first()
later_msg = session.query(MessageSql).filter(MessageSql.message_id == later_id).first()


first_msg.payload['DataChannelList'][0]['Version'] == '000'
later_msg.payload['DataChannelList'][0]['Version'] == '001'

'TerminalAssetAlias' not in first_msg.payload['DataChannelList'][0].keys()
'TerminalAssetAlias' in later_msg.payload['DataChannelList'][0].keys()

later_br: BatchedReadings = from_dict(later_msg.payload)

assert type(later_br) == BatchedReadings

later_dcs = [pyd_to_sql(dc) for dc in later_br.data_channel_list]

data_channels_match_db(session, later_dcs)