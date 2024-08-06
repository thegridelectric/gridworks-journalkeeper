from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session
from gjk.models import MessageSql, ReadingSql
import pendulum
import dotenv
from gjk.models import MessageSql, ReadingSql
from gjk.models import DataChannelSql
from gjk.config import Settings
from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, BigInteger, Integer, String, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import UniqueConstraint
from datetime import datetime
import pandas as pd

# ------------------------------------------
# User inputs
# ------------------------------------------

timezone = 'America/New_York'
start= pendulum.datetime(2024, 2, 1, 0, 0, tz=timezone)
end = pendulum.datetime(2024, 2, 2, 20, 0, tz=timezone)

# ------------------------------------------
# Import readings data
# ------------------------------------------

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

saved_sql_channels = session.query(DataChannelSql).all()
saved_channel_ids = [channel.id for channel in saved_sql_channels]

# Convert to Unix timestamp in milliseconds
start_ms = int(start.timestamp() * 1000)
end_ms = int(end.timestamp() * 1000)

readings = session.query(ReadingSql).filter(
    ReadingSql.time_ms >= start_ms,
    ReadingSql.time_ms < end_ms,
).order_by(asc(ReadingSql.time_ms)).all()

# ------------------------------------------
# Split the data by channel
# ------------------------------------------

power_channels = ['hp-idu', 'hp-odu', 'dist-pump', 'primary-pump', 'store-pump']

power_data = {}
time_data = {}
for p in power_channels:
    pwr_values = []
    pwr_times = []
    for r in readings:
        if p in r.data_channel.name:
            pwr_values.append(r.value)
            pwr_times.append(r.time_ms)
    power_data[f'{p}'] = pwr_values
    time_data[f'{p}'] = pwr_times

# ------------------------------------------
# For every hour, convert to energy
# ------------------------------------------

energy_results = {}

first_hour = start.in_tz('UTC').naive()
last_hour = end.in_tz('UTC').naive()
num_hours = int((last_hour-first_hour).total_hours())
hour_data = [first_hour.add(hours=x) for x in range(num_hours)]

for p in power_channels:
    
    energy_results[f'{p}'] = []
    last_power_before_current_hour = 0
    time_data_hours = [datetime.fromtimestamp(x/1000).replace(minute=0, second=0, microsecond=0) for x in time_data[f'{p}']]

    for hour in range(num_hours):
        
        current_hour = first_hour.add(hours=hour)
        next_hour = first_hour.add(hours=hour+1)

        # Isolate data for the given hour
        times_for_this_hour = [time_data[f'{p}'][i] for i in range(len(time_data[f'{p}'])) if time_data_hours[i]==current_hour]
        powers_for_this_hour = [power_data[f'{p}'][i] for i in range(len(power_data[f'{p}'])) if time_data_hours[i]==current_hour]

        # Add points at the start and end of the hour
        times_for_this_hour = [current_hour.timestamp()*1000] + times_for_this_hour + [next_hour.timestamp()*1000]
        powers_for_this_hour = [last_power_before_current_hour] + powers_for_this_hour + [powers_for_this_hour[-1]]
        last_power_before_current_hour = powers_for_this_hour[-1] # for the next hour

        # Compute the energy for the given hour
        time_diff_hours = [(y-x)/1000/60/60 for x,y in zip(times_for_this_hour[:-1], times_for_this_hour[1:])]
        energy = round(sum([powers_for_this_hour[i] * time_diff_hours[i] for i in range(len(time_diff_hours))]),2)
        energy_results[f'{p}'].append(0 if energy<0 else energy)

# ------------------------------------------
# Convert the results to a dataframe
# ------------------------------------------

df = pd.DataFrame({'id':[], 'hour_start_s':[], 'channel_name':[], 'watt_hours':[], 'g_node_alias':[]})
for p in power_channels:
    for h in range(len(hour_data)):

        g_node = 'd1.isone.ver.keene.beech'
        channel = p+'-energy'
        hour_start = int(hour_data[h].timestamp())
        value = int(energy_results[f'{p}'][h])
        id = f"{g_node}_{hour_start}_{channel}"

        row = [id, hour_start, channel, value, g_node]
        df.loc[len(df)] = row

df = df.sort_values(by='g_node_alias')
print(df)
df.to_csv('thomas.csv')
# pas de 0!

df = pd.read_csv('/Users/thomas/Desktop/thomas.csv')
df.drop(columns=['Unnamed: 0'], axis=1, inplace=True)

# ------------------------------------------
# Add to the database
# ------------------------------------------

def add_row(row_data):

    energy_row_sqlalchemy = GWPowerSQLAlchemy(
        id = row_data[0],
        hour_start_s = row_data[1], 
        channel_name = row_data[2],
        watt_hours = int(row_data[3]), # remove this later
        g_node_alias = row_data[4])
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(energy_row_sqlalchemy)
    session.commit()
    session.close()

Base = declarative_base()
class GWPowerSQLAlchemy(Base):
    __tablename__ = 'hourly_device_energy'
    id = Column(String, primary_key=True)
    hour_start_s = Column(BigInteger)
    channel_name = Column(String)
    watt_hours = Column(Integer)
    g_node_alias = Column(String)
    __table_args__ = (
        UniqueConstraint('hour_start_s', 'channel_name', 'g_node_alias', name='unique_time_channel_gnode'),
    )

engine = create_engine('postgresql://thomas@localhost/thomas')
Base.metadata.drop_all(engine) # remove existing table
Base.metadata.create_all(engine) # add new table

for index, row in df.iterrows():
    add_row(row.tolist())