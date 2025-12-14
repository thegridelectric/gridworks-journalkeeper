import copy

import dotenv
import pendulum
from gjk.config import Settings
from gjk.first_season.beech_channels import (
    BEECH_CHANNELS_BY_NAME,
)
from gjk.models import MessageSql
from sqlalchemy import asc, create_engine
from sqlalchemy.orm import sessionmaker

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)

if __name__ == "__main__":
    session = Session()

    start_ms = (
        pendulum.datetime(2024, 4, 26, 0, 0, 0, tz="America/New_York").int_timestamp
        * 1000
    )
    end_ms = start_ms + 24 * 60 * 60 * 1000

    while True:
        print(pendulum.from_timestamp(start_ms / 1000))

        messages = (
            session.query(MessageSql)
            .filter(
                MessageSql.message_persisted_ms >= start_ms,
                MessageSql.message_persisted_ms < end_ms,
            )
            .order_by(asc(MessageSql.message_persisted_ms))
            .all()
        )

        if messages:
            print(f"Updating {len(messages)} messages...")
        else:
            print("No messages on this day.")
            break

        for message in messages:
            message_edit = copy.deepcopy(message)

            if "DataChannelList" in message_edit.payload:
                for dc in message_edit.payload["DataChannelList"]:
                    for key, value in BEECH_CHANNELS_BY_NAME.items():
                        if value.id == dc["Id"]:
                            name = key
                    dc["TerminalAssetAlias"] = BEECH_CHANNELS_BY_NAME[
                        name
                    ].terminal_asset_alias
                    dc["Version"] = BEECH_CHANNELS_BY_NAME[name].version
                    dc["CapturedByNodeName"] = BEECH_CHANNELS_BY_NAME[
                        name
                    ].captured_by_node_name
                    dc["DisplayName"] = BEECH_CHANNELS_BY_NAME[name].display_name
                    dc["AboutNodeName"] = BEECH_CHANNELS_BY_NAME[name].about_node_name
                    dc["Name"] = BEECH_CHANNELS_BY_NAME[name].name

            message.payload = message_edit.payload

        print("Committing the changes...")
        session.commit()
        print("Done.\n")

        start_ms += 24 * 60 * 60 * 1000
        end_ms += 24 * 60 * 60 * 1000

    session.close()
