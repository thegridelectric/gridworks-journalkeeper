import json
import subprocess
import pandas as pd
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
from gjk.models import ReadingSql, DataChannelSql, MessageSql

GRIDWORKS_DEV_OPS_GENIE_TEAM_ID = "edaccf48-a7c9-40b7-858a-7822c6f862a4"
HOUSES = ['oak']
dist_flow_after_heat_call = {}
num_alerts = 0
alerts = {}
MIN_POWER_KW = 2

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()

def send_opsgenie_alert(house_alias, heat_call_time):
    # Create OpsGenie client configuration
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]

    payload = {
        "message": f"[{house_alias}] No dist-flow has been recorded after a heat call at {heat_call_time}.",
        "alias": "dist-flow",
        "priority": "P1",
        "responders": responders,
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Check for successful response
    if response.status_code == 202:
        print("Alert sent successfully!")
    else:
        print(
            f"Failed to send alert. Status code: {response.status_code}, Response: {response.text}"
        )

def check_distflow():

    global num_alerts

    for house_alias in HOUSES:

        print(f"\n{house_alias}\n")
        if house_alias not in alerts:
            alerts[house_alias] = []

        # Get all the data you need
        start_ms = pendulum.now(tz='America/New_York').add(days=-1).timestamp() * 1000
        messages = session.query(MessageSql).filter(
            MessageSql.from_alias.like(f'%{house_alias}%'),
            or_(
                MessageSql.message_type_name == "batched.readings",
                MessageSql.message_type_name == "report"
                ),
            MessageSql.message_persisted_ms >= start_ms,
        ).order_by(asc(MessageSql.message_persisted_ms)).all()
        channels = {}
        for message in messages:
            for channel in message.payload['ChannelReadingList']:
                # Find the channel name
                if message.message_type_name == 'report':
                    channel_name = channel['ChannelName']
                elif message.message_type_name == 'batched.readings':
                    for dc in message.payload['DataChannelList']:
                        if dc['Id'] == channel['ChannelId']:
                            channel_name = dc['Name']
                # Store the values and times for the channel
                if ('zone' in channel_name and 'state' in channel_name) or (channel_name=='dist-pump-pwr'):
                    if channel_name not in channels:
                        channels[channel_name] = {
                            'values': channel['ValueList'],
                            'times': channel['ScadaReadTimeUnixMsList']
                        }
                    else:
                        channels[channel_name]['values'].extend(channel['ValueList'])
                        channels[channel_name]['times'].extend(channel['ScadaReadTimeUnixMsList'])
        # Sort values according to time
        for key in channels.keys():
            sorted_times_values = sorted(zip(channels[key]['times'], channels[key]['values']))
            sorted_times, sorted_values = zip(*sorted_times_values)
            channels[key]['values'] = list(sorted_values)
            channels[key]['times'] = list(sorted_times)
        
        # Find the last heat call in the house
        last_heatcall_time = 0
        for zone in [channels[channel] for channel in channels.keys() if 'zone' in channel]:
            last_heatcall_zone = [
                        zone['times'][i] 
                        for i in range(len(zone['times']))
                        if zone['values'][i]==1]
            if last_heatcall_zone:
                if last_heatcall_zone[-1] > last_heatcall_time:
                    last_heatcall_time = last_heatcall_zone[-1]
        if last_heatcall_time>0:
            print(f"Last heat call for {house_alias}: {pendulum.from_timestamp(last_heatcall_time/1000, tz='America/New_York')}")
        else:
            print(f"The last heat call at {house_alias} was more than 24 hours ago.")

        # Try to find flow data around the last heat call
        for flow in [channels[channel] for channel in channels.keys() if 'dist-pump-pwr' in channel]:
            flow_around_heatcall = [
                flow['values'][i] 
                for i in range(len(flow['times']))
                if flow['times'][i]>=last_heatcall_time-10*60*1000]
            print(f'Found {len(flow_around_heatcall)} power reports at some point in time in [heatcall-10min, now]')
            print(flow_around_heatcall)
            if not flow_around_heatcall:
                # Check the last value before heatcall-10min
                last_flow_before_hc10 = [
                    flow['values'][i] 
                    for i in range(len(flow['times']))
                    if flow['times'][i]<=last_heatcall_time-10*60*1000][-1]
                # If the last value reported means the dist pump was off
                if last_flow_before_hc10 <= MIN_POWER_KW:
                    alerts[house_alias].append(last_heatcall_time)
            else:
                # Check if there was really power
                if max(flow_around_heatcall) <= MIN_POWER_KW:
                    alerts[house_alias].append(last_heatcall_time)
                # Reset the alert to 0 if there was flow around the last heat call
                else:
                    alerts[house_alias] = []

        # Send Opsgenie alert if there have been three alerts
        if len(alerts[house_alias])==3:
            print(f'[ALERT] There are 3 unsatisfied heat calls at {house_alias}!')
            send_opsgenie_alert(house_alias, pendulum.from_timestamp(last_heatcall_time/1000, tz='America/New_York'))

        print(f"Done for {house_alias}.")


        # # Find the datachannels in the given house
        # data_channels = session.query(DataChannelSql).filter(
        #     DataChannelSql.terminal_asset_alias.like(f'%{house_alias}%')
        #     ).all()
        # if not data_channels:
        #     raise ValueError(f'No data channels found for {house_alias}')

        # # Find the last heat call in the house
        # for channel in [dc for dc in data_channels if 'zone' in dc.name and 'state' in dc.name]:
        #     start_ms = pendulum.now().add(weeks=-1).timestamp() * 1000
        #     if 'zone' in channel.name:
        #         last_reading = session.query(ReadingSql).filter(
        #             ReadingSql.data_channel_id.like(channel.id),
        #             ReadingSql.value == 1,
        #             ReadingSql.time_ms >= start_ms,
        #         ).order_by(desc(ReadingSql.time_ms)).first()
        #         if last_reading.time_ms > last_heatcall_time[house_alias]:
        #             last_heatcall_time[house_alias] = last_reading.time_ms
        # print(f"Last heat call for {house_alias}: {pendulum.from_timestamp(last_heatcall_time[house_alias]/1000, tz='America/New_York')}")

        # # Try to find data after the last heat call (TODO: if you don't look before it)
        # for channel in [dc for dc in data_channels if dc.name=='dist-flow']:
        #     start_ms = last_heatcall_time[house_alias]
        #     end_ms = last_heatcall_time[house_alias] + 5*60*1000
        #     dist_flow_data = session.query(ReadingSql).filter(
        #         ReadingSql.data_channel_id.like(channel.id),
        #         ReadingSql.time_ms >= start_ms,
        #         ReadingSql.time_ms <= end_ms,
        #     ).order_by(desc(ReadingSql.time_ms)).all()
        #     print(f"Found {len(dist_flow_data)} dist-flow readings in the 5 minutes after that heat call.")
        #     if len(dist_flow_data)==0:
        #         print(f"We have a problem at {house_alias}!")
        #         send_opsgenie_alert(house_alias, 
        #                             pendulum.from_timestamp(last_heatcall_time[house_alias]/1000, tz='America/New_York'))

if __name__ == '__main__':
    while(True):
        check_distflow()
        time.sleep(5*60)
