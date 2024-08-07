from gjk.models import ReadingSql
from gjk.models import DataChannelSql
from gjk.models import HourlyEnergySql
from gjk.models import bulk_insert_hourly_energy
from gjk.enums import TelemetryName
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import asc
from typing import List, Dict
import pendulum
import dotenv
import os

# ------------------------------------------
# User inputs
# ------------------------------------------

timezone = 'America/New_York'
start = pendulum.datetime(2024, 2, 1, 0, 0, tz=timezone)
end = pendulum.datetime(2024, 2, 2, 20, 0, tz=timezone)

# Record 0 Wh values in the energy table
record_zeros = False

# ------------------------------------------
# Import power readings by channel
# ------------------------------------------

dotenv.load_dotenv()
engine = create_engine(os.getenv('GJK_DB_URL'))
Session = sessionmaker(bind=engine)
session = Session()

saved_sql_channels = session.query(DataChannelSql).all()
saved_channel_ids = [channel.id for channel in saved_sql_channels]

# Convert to Unix timestamp in milliseconds
start_ms = int(start.timestamp() * 1000)
end_ms = int(end.timestamp() * 1000)

# Find the power channels
from gjk.first_season.beech_channels import BEECH_CHANNELS_BY_NAME
power_channels = []
for channel in BEECH_CHANNELS_BY_NAME:
    if BEECH_CHANNELS_BY_NAME[channel].telemetry_name == TelemetryName.PowerW.value:
        power_channels.append(BEECH_CHANNELS_BY_NAME[channel])

# Store the readings by channel in a dictionnary 
power_readings: Dict[DataChannelSql, List[ReadingSql]] = {}
for channel in power_channels:
    power_readings[channel] = session.query(ReadingSql).filter(
        ReadingSql.time_ms >= start_ms,
        ReadingSql.time_ms < end_ms,
        ReadingSql.data_channel_id == channel.id
        ).order_by(asc(ReadingSql.time_ms)).all()

# ------------------------------------------
# For every hour, convert to energy
# ------------------------------------------

energy_results = {}
num_hours = int((end-start).total_hours())

for channel in power_channels:
    
    energy_results[channel] = []
    time_data_hours = [pendulum.from_timestamp(x.time_ms/1000).replace(minute=0, second=0, microsecond=0) for x in power_readings[channel]]

    # Find the last power value recorded before the requested start time
    past_hours = 1
    past_power_readings: List[ReadingSql] = []
    while past_power_readings == []:
        try:
            past_power_readings = session.query(ReadingSql).filter(
                ReadingSql.time_ms >= int(start.add(hours=-past_hours).timestamp() * 1000),
                ReadingSql.time_ms < start_ms,
                ReadingSql.data_channel_id == channel.id
                ).order_by(asc(ReadingSql.time_ms)).all()
            if past_hours > 30*24:
                last_power_before_current_hour = 0
                print('No previous power data has been found within the 30 days before start date.\nAssuming the power was 0 W just before the start date.')
                break
        except Exception as e:
            print(f"Could not retrieve data {past_hours} hours before start date.\nAssuming the power was 0 W just before the start date.\n{e}")
            last_power_before_current_hour = 0
        past_hours += 1
    if past_power_readings:
        last_power_before_current_hour = [r.value for r in past_power_readings][-1]

    for hour in range(num_hours):
        
        current_hour = start.add(hours=hour)
        next_hour = start.add(hours=hour+1)

        # Isolate data for the given hour
        times_for_this_hour = [r.time_ms for i,r in enumerate(power_readings[channel]) if time_data_hours[i]==current_hour]
        powers_for_this_hour = [r.value for i,r in enumerate(power_readings[channel]) if time_data_hours[i]==current_hour]

        # Add points at the start and end of the hour
        times_for_this_hour = [current_hour.timestamp()*1000] + times_for_this_hour + [next_hour.timestamp()*1000]
        if powers_for_this_hour:
            powers_for_this_hour = [last_power_before_current_hour] + powers_for_this_hour + [powers_for_this_hour[-1]]
            last_power_before_current_hour = powers_for_this_hour[-1] # for the next hour
        else:
            powers_for_this_hour = [last_power_before_current_hour] + powers_for_this_hour + [last_power_before_current_hour]

        # Compute the energy for the given hour
        time_diff_hours = [(y-x)/1000/60/60 for x,y in zip(times_for_this_hour[:-1], times_for_this_hour[1:])]
        energy = round(sum([powers_for_this_hour[i] * time_diff_hours[i] for i in range(len(time_diff_hours))]),2)
        energy_results[channel].append(0 if energy<0 else energy)

# ------------------------------------------
# Add the results to the database
# ------------------------------------------

# Create a list of HourlyEnergySql objects to insert
hourly_energy_list = []

for h in range(num_hours):
    for channel in power_channels:

        g_node = 'd1.isone.ver.keene.beech'
        channel_name_energy = channel.name+'-energy' # check with Jessica what channel name we want
        hour_start = int(start.add(hours=h).timestamp())
        value = int(energy_results[channel][h])
        id = f"{g_node}_{hour_start}_{channel_name_energy}"

        if value > 0 or record_zeros:
            print([id, hour_start, channel_name_energy, value, g_node])

            hourly_energy = HourlyEnergySql(
                    id = id,
                    hour_start_s = hour_start, 
                    channel_name = channel_name_energy,
                    watt_hours = value,
                    g_node_alias = g_node)
            
            hourly_energy_list.append(hourly_energy)

# Add the list to the database
engine = create_engine('postgresql://thomas@localhost/thomas')
Session = sessionmaker(bind=engine)
session = Session()
bulk_insert_hourly_energy(session, hourly_energy_list)