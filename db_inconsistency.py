import copy
import dotenv
from gjk.codec import from_dict, pyd_to_sql
from gjk.config import Settings
from gjk.first_season.beech_channels import BEECH_CHANNELS_BY_NAME, data_channels_match_db
from gjk.models import MessageSql
from gjk.types import BatchedReadings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)

def update_message(session, message_id):

    try:
        message = session.query(MessageSql).filter(MessageSql.message_id == message_id).first()
        message_edit = copy.deepcopy(message)

        if 'Watts' in message_edit.payload:
            return

        # Edit the datachannel list
        for dc in message_edit.payload['DataChannelList']:
            for key, value in BEECH_CHANNELS_BY_NAME.items():
                if value.id == dc["Id"]:
                    name = key
            
            # if "TerminalAssetAlias" in dc and dc["TerminalAssetAlias"] != BEECH_CHANNELS_BY_NAME[name].terminal_asset_alias:
            #     print(f"Before: {dc["TerminalAssetAlias"]}\nAfter: {BEECH_CHANNELS_BY_NAME[name].terminal_asset_alias}")
            # if "Version" in dc and dc["Version"] != BEECH_CHANNELS_BY_NAME[name].version:
            #     print(f"Before: {dc["Version"]}\nAfter: {BEECH_CHANNELS_BY_NAME[name].version}")
            # if "CapturedByNodeName" in dc and dc["CapturedByNodeName"] != BEECH_CHANNELS_BY_NAME[name].captured_by_node_name:
            #     print(f"Before: {dc["CapturedByNodeName"]}\nAfter: {BEECH_CHANNELS_BY_NAME[name].captured_by_node_name}")
            # if "DisplayName" in dc and dc["DisplayName"] != BEECH_CHANNELS_BY_NAME[name].display_name:
            #     print(f"Before: {dc["DisplayName"]}\nAfter: {BEECH_CHANNELS_BY_NAME[name].display_name}")
            # if "AboutNodeName" in dc and dc["AboutNodeName"] != BEECH_CHANNELS_BY_NAME[name].about_node_name:
            #     print(f"Before: {dc["AboutNodeName"]}\nAfter: {BEECH_CHANNELS_BY_NAME[name].about_node_name}")
            # if "Name" in dc and dc["Name"] != BEECH_CHANNELS_BY_NAME[name].name:
            #     print(f"Before: {dc["Name"]}\nAfter: {BEECH_CHANNELS_BY_NAME[name].name}")
        
            dc["TerminalAssetAlias"] = BEECH_CHANNELS_BY_NAME[name].terminal_asset_alias
            dc["Version"] = BEECH_CHANNELS_BY_NAME[name].version
            dc["CapturedByNodeName"] = BEECH_CHANNELS_BY_NAME[name].captured_by_node_name
            dc["DisplayName"] = BEECH_CHANNELS_BY_NAME[name].display_name
            dc["AboutNodeName"] = BEECH_CHANNELS_BY_NAME[name].about_node_name
            dc["Name"] = BEECH_CHANNELS_BY_NAME[name].name

        if message.payload == message_edit.payload:
            print(f"[ok] Message {message_id} was already up to date.")
            return

        # Check it matches local db
        first_br: BatchedReadings = from_dict(message_edit.payload)
        dc_list_check = [pyd_to_sql(dc) for dc in first_br.data_channel_list]
        data_channels_match_db(session, dc_list_check, check_missing=False)

        # Save and commit
        message.payload = message_edit.payload
        session.commit()

        # Check the changes
        check_msg = session.query(MessageSql).filter(MessageSql.message_id == message_id).first()
        if check_msg.payload["DataChannelList"] == message_edit.payload['DataChannelList']:
            print(f"[ok] Message {message_id} updated successfully.")
        else:
            print("Error")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"An error occurred: {e}")
    

if __name__ == "__main__":
    session = Session()
    
    offset = 0
    batch_size = 100
    
    while True:
        messages = session.query(MessageSql).offset(offset).limit(batch_size).all()
        if not messages:
            break

        for message in messages:
            update_message(session, message.message_id)

        offset += batch_size
        print(f"Processed messages {offset-batch_size} to {offset}")
    
    session.close()
