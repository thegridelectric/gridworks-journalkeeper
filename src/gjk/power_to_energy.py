from gjk.models import ReadingSql
from gjk.models import DataChannelSql
from gjk.models import HourlyEnergySql
from gjk.models import bulk_insert_hourly_energy
from gjk.enums import TelemetryName
from gjk.first_season.beech_channels import BEECH_CHANNELS_BY_NAME
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import asc
from typing import List, Dict
import pendulum
import dotenv
import os

def add_to_hourly_energy_table(session, start:pendulum.DateTime=pendulum.now(), end:pendulum.DateTime=pendulum.now(), time_delta:int=10):

    # If there is no specified start time, use the time_delta
    start = start if start.replace(microsecond=0)<end.replace(microsecond=0) else end.add(hours=-time_delta)

    # Record 0 Wh values in the energy table
    record_zeros = True

    # ------------------------------------------
    # Import power readings by channel
    # ------------------------------------------

    saved_sql_channels = session.query(DataChannelSql).all()
    saved_channel_ids = [channel.id for channel in saved_sql_channels]

    # Convert to Unix timestamp in milliseconds
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    # Store the readings by channel in a dictionnary 
    power_channels = [channel for channel in BEECH_CHANNELS_BY_NAME.values() if channel.telemetry_name == TelemetryName.PowerW.value]
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
        past_days = 60
        past_power_readings: List[ReadingSql] = session.query(ReadingSql).filter(
            ReadingSql.time_ms >= int(start.add(hours=-past_days*24).timestamp() * 1000),
            ReadingSql.time_ms < start_ms,
            ReadingSql.data_channel_id == channel.id
            ).order_by(asc(ReadingSql.time_ms)).all()
        if past_power_readings:
            last_power_before_current_hour = past_power_readings[-1].value
        else:
            last_power_before_current_hour = 0
            print(f'No data for {channel.name} has been found within the {past_days} days before start datetime. Assuming no power just before the start datetime.')

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

            # Treat negative power values
            for i in range(len(powers_for_this_hour)):
                if powers_for_this_hour[i] < 0:
                    if powers_for_this_hour[i] > -2.5:
                        powers_for_this_hour[i] = 0
                    else:
                        #raise ValueError(f"The value for {channel.name} at time {times_for_this_hour[i]} is {powers_for_this_hour[i]} W")
                        print(f"The value for {channel.name} at time {times_for_this_hour[i]} is {powers_for_this_hour[i]} W")

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
            channel_name = channel.name
            hour_start = int(start.add(hours=h).timestamp())
            value = int(energy_results[channel][h])
            id = f"{g_node}_{hour_start}_{channel_name}"

            if value > 0 or record_zeros:
                print([id, hour_start, channel_name, value, g_node])

                hourly_energy = HourlyEnergySql(
                        id = id,
                        hour_start_s = hour_start, 
                        power_channel = channel_name,
                        watt_hours = value,
                        g_node_alias = g_node)
                
                hourly_energy_list.append(hourly_energy)

    # Add the list to the database
    engine = create_engine('postgresql://thomas@localhost/thomas')
    Session = sessionmaker(bind=engine)
    session = Session()
    bulk_insert_hourly_energy(session, hourly_energy_list)


if __name__ == "__main__":

    dotenv.load_dotenv()
    engine = create_engine(os.getenv('GJK_DB_URL'))
    Session = sessionmaker(bind=engine)
    session = Session()

    timezone = 'America/New_York'
    start = pendulum.datetime(2024, 2, 1, 0, 0, tz=timezone)
    end = pendulum.datetime(2024, 2, 2, 20, 0, tz=timezone)

    add_to_hourly_energy_table(session, start, end)