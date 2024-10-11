import dotenv
import pendulum
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from gjk.config import Settings
from gjk.models import MessageSql, ReadingSql, bulk_insert_readings
import uuid

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

timezone = "America/New_York"
start = pendulum.datetime(2024, 1, 1, 0, 0, tz=timezone)

for k in range(10):

    start_k = start.add(days=k)
    end_k = start.add(days=k+1)
    start_ms = int(start_k.timestamp() * 1000)
    end_ms = int(end_k.timestamp() * 1000)

    print(f"\nLoading readings from {start_k}")

    messages = session.query(MessageSql).filter(
        MessageSql.from_alias.like(f'%beech%'),
        MessageSql.message_persisted_ms >= start_ms,
        MessageSql.message_persisted_ms <= end_ms,
    ).order_by(asc(MessageSql.message_persisted_ms)).all()

    print(f"Found {len(messages)} messages. Processing...")

    if messages:
        readings = []
        for message in messages:
            for readings_by_channel in message.payload['ChannelReadingList']:
                for i in range(len(readings_by_channel['ValueList'])):
                    reading = ReadingSql(
                        id=str(uuid.uuid4()),
                        value = readings_by_channel['ValueList'][i],
                        time_ms = readings_by_channel['ScadaReadTimeUnixMsList'][i],
                        data_channel_id = readings_by_channel['ChannelId'],
                        message_id = message.message_id
                        )
                    readings.append(reading)

        print(f"Inserting {len(readings)} readings")
        bulk_insert_readings(session=session, reading_list=readings)
    
    print("Done.")