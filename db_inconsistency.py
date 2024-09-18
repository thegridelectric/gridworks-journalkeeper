import copy
import dotenv
import pendulum
from gjk.codec import from_dict, pyd_to_sql
from gjk.config import Settings
from gjk.first_season.beech_channels import BEECH_CHANNELS_BY_NAME, data_channels_match_db
from gjk.models import MessageSql
from gjk.types import BatchedReadings
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)

if __name__ == "__main__":
    
    session = Session()

    start_ms = pendulum.datetime(2023, 11, 13, 0, 0, 0, tz="America/New_York").int_timestamp*1000
    end_ms = start_ms + 24*60*60*1000
        
    while True:

        messages = session.query(MessageSql).filter(MessageSql.message_persisted_ms >= start_ms,
                                                    MessageSql.message_persisted_ms < end_ms).order_by(asc(MessageSql.message_persisted_ms)).all()
                
        if messages:
            print(pendulum.from_timestamp(start_ms/1000))
            print(f"Updating {len(messages)} messages...")
        else:
            print(f"No messages on {pendulum.from_timestamp(start_ms/1000)}")
            break
        
        for message in messages: 

            message_edit = copy.deepcopy(message)

            if 'DataChannelList' in message_edit.payload:
                for dc in message_edit.payload['DataChannelList']:
                    for key, value in BEECH_CHANNELS_BY_NAME.items():
                        if value.id == dc["Id"]:
                            name = key
                    dc["TerminalAssetAlias"] = BEECH_CHANNELS_BY_NAME[name].terminal_asset_alias
                    dc["Version"] = BEECH_CHANNELS_BY_NAME[name].version
                    dc["CapturedByNodeName"] = BEECH_CHANNELS_BY_NAME[name].captured_by_node_name
                    dc["DisplayName"] = BEECH_CHANNELS_BY_NAME[name].display_name
                    dc["AboutNodeName"] = BEECH_CHANNELS_BY_NAME[name].about_node_name
                    dc["Name"] = BEECH_CHANNELS_BY_NAME[name].name
            
            message.payload = message_edit.payload

        session.commit()
        
        start_ms += 24*60*60*1000
        end_ms += 24*60*60*1000
    
    session.close()
