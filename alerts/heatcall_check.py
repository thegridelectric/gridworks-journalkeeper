import json
import subprocess
import time
import dotenv
import pendulum
import requests
from pydantic import BaseModel
from sqlalchemy import create_engine, desc, asc, or_
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt
from datetime import timedelta
import numpy as np
from typing import List
from gjk.config import Settings
from gjk.models import ReadingSql, DataChannelSql

HOUSES = ['beech', 'oak', 'fir']
last_heat_call_time_ms = {}
dist_flow_after_heat_call = {}

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

for house_alias in HOUSES:

    print(f"\n{house_alias}\n")
    last_heat_call_time_ms[house_alias] = 0

    # Find the datachannels in the given house
    data_channels = session.query(DataChannelSql).filter(
        DataChannelSql.terminal_asset_alias.like(f'%{house_alias}%')
        ).all()
    if not data_channels:
        raise ValueError(f'No data channels found for {house_alias}')

    # Find the last heat call in the house
    for channel in [dc for dc in data_channels if 'zone' in dc.name and 'state' in dc.name]:
        print(channel.name)
        start_ms = pendulum.now().add(weeks=-1).timestamp() * 1000
        if 'zone' in channel.name:
            last_reading = session.query(ReadingSql).filter(
                ReadingSql.data_channel_id.like(channel.id),
                ReadingSql.value == 1,
                ReadingSql.time_ms >= start_ms,
            ).order_by(desc(ReadingSql.time_ms)).first()
            print(last_reading.time_ms)
            if last_reading.time_ms > last_heat_call_time_ms[house_alias]:
                last_heat_call_time_ms[house_alias] = last_reading.time_ms
    print("Latest:", last_heat_call_time_ms[house_alias]/1000)

    print(f"Last heat call for {house_alias}: {pendulum.from_timestamp(last_heat_call_time_ms[house_alias]/1000, tz='America/New_York')}")

    # Try to find data after the last heat call (TODO: if you don't look before it)
    for channel in [dc for dc in data_channels if dc.name=='dist-flow']:
        start_ms = last_heat_call_time_ms[house_alias]
        end_ms = last_heat_call_time_ms[house_alias] + 5*60*1000
        dist_flow_data = session.query(ReadingSql).filter(
            ReadingSql.data_channel_id.like(channel.id),
            ReadingSql.time_ms >= start_ms,
            ReadingSql.time_ms <= end_ms,
        ).order_by(desc(ReadingSql.time_ms)).all()
        print(f"Read {len(dist_flow_data)} dist-flow points in the 5 minutes after that heat call.")
