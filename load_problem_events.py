import dotenv
import pendulum
from gjk.journal_keeper_hack import JournalKeeperHack
from gjk.config import Settings
from gjk.models import MessageSql, bulk_insert_messages
from sqlalchemy import asc, create_engine
from sqlalchemy.orm import sessionmaker
# from gwproto.messages import ProblemEvent

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

timezone = "America/New_York"
start = pendulum.datetime(2024, 12, 22, 0, 0, tz=timezone)

for house_alias in ['beech','oak','fir']:

    for k in range(10):
        start_k = start.add(hours=12*k)
        start_s = int(start_k.timestamp())
        print(f"\nLoading problem event messages from {start_k}")

        hack = JournalKeeperHack(Settings(_env_file=dotenv.find_dotenv()), alias=house_alias)
        pb_event_messages = hack.load_messages_from_s3(
            start_s=start_s,
            duration_hrs=12,
            short_alias=house_alias
            )

        if pb_event_messages is not None and pb_event_messages != []:
            print(f"Found {len(pb_event_messages)} messages which are ProblemEvents")
            print(f"Inserting {len(pb_event_messages)} problem event messages...")
            bulk_insert_messages(db=session, message_list=pb_event_messages)

        print("Done.")
    
    print(f"Done for {house_alias}!")
