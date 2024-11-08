import json
import time
import dotenv
import pendulum
import requests
from gjk.config import Settings
from gjk.models import MessageSql
from sqlalchemy import asc, create_engine, or_
from sqlalchemy.orm import sessionmaker

GRIDWORKS_DEV_OPS_GENIE_TEAM_ID = "edaccf48-a7c9-40b7-858a-7822c6f862a4"
MAX_DIFFERENCE_F = 2
RUN_EVERY_MIN = 10
warnings = {}

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()


def send_opsgenie_alert(house_alias, zone):
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]
    payload = {
        "message": f"[{house_alias}] {zone} is getting cold!",
        "alias": "dist-flow",
        "priority": "P1",
        "responders": responders,
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 202:
        print("Alert sent successfully")
    else:
        print(
            f"Failed to send alert. Status code: {response.status_code}, Response: {response.text}"
        )

def send_opsgenie_warning(message):
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]
    payload = {
        "message": message,
        "alias": "dist-flow",
        "priority": "P5",
        "responders": responders,
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 202:
        print("Warning sent successfully")
    else:
        print(
            f"Failed to send warning. Status code: {response.status_code}, Response: {response.text}"
        )


def check_setpoint():
    global warnings

    # Get the data
    start_ms = pendulum.now(tz="America/New_York").add(hours=-2).timestamp() * 1000
    messages = (
        session.query(MessageSql)
        .filter(
            or_(
                MessageSql.message_type_name == "batched.readings",
                MessageSql.message_type_name == "report",
            ),
            MessageSql.message_persisted_ms >= start_ms,
        )
        .order_by(asc(MessageSql.message_persisted_ms))
        .all()
    )

    if not messages:
        print(f"No messages found.")
        return

    # For every house
    all_house_aliases = list({x.from_alias for x in messages})
    all_house_aliases = [x.split(".")[-2] for x in all_house_aliases]
    for house_alias in all_house_aliases:
        print(f"\n{house_alias}\n")
        if house_alias not in warnings:
            warnings[house_alias] = {}
        channels = {}

        # Store times and values for every channel
        for message in [m for m in messages if house_alias in m.from_alias]:
            for channel in message.payload["ChannelReadingList"]:
                # Find the channel name
                if message.message_type_name == "report":
                    channel_name = channel["ChannelName"]
                elif message.message_type_name == "batched.readings":
                    for dc in message.payload["DataChannelList"]:
                        if dc["Id"] == channel["ChannelId"]:
                            channel_name = dc["Name"]
                # Store the times and values
                if ("zone" in channel_name):
                    if channel_name not in channels:
                        channels[channel_name] = {
                            "values": channel["ValueList"],
                            "times": channel["ScadaReadTimeUnixMsList"],
                        }
                    else:
                        channels[channel_name]["values"].extend(channel["ValueList"])
                        channels[channel_name]["times"].extend(
                            channel["ScadaReadTimeUnixMsList"]
                        )
        # Sort according to time
        for key in channels.keys():
            sorted_times_values = sorted(
                zip(channels[key]["times"], channels[key]["values"])
            )
            sorted_times, sorted_values = zip(*sorted_times_values)
            channels[key]["values"] = list(sorted_values)
            channels[key]["times"] = list(sorted_times)

        # Isolate by zone
        zones = {}
        for key in channels.keys():
            if key[:5] not in zones:
                zones[key[:5]] = [key]
            else:
                zones[key[:5]].append(key)

        # Check if right now the room temperatures are at or above setpoint every sampling period
        for zone in zones.keys():
            print(zone)
            temp_much_lower_than_set = False
            for temp in zones[zone]:
                if 'set' in temp:
                    setpoint = channels[temp]['values'][-1]/1000
                    setpoint = round(setpoint) if round(setpoint)==setpoint else setpoint
                if 'temp' in temp and 'gw' not in temp:
                    temperature = channels[temp]['values'][-1]/1000
            if setpoint - temperature >= MAX_DIFFERENCE_F and zone not in warnings[house_alias]:
                temp_much_lower_than_set = True
                print(f'Potential problem! {setpoint} >= {temperature}+{MAX_DIFFERENCE_F}')
            elif setpoint <= temperature and zone in warnings[house_alias]:
                print(f"[Ok] Setpoint in {zone} has now been reached")
                # send_opsgenie_warning(
                #     f"[{house_alias}] Setpoint in {zone} has now been reached."
                # )
                del warnings[house_alias][zone]
            
            # Check if the user turned up the thermostat recently
            if temp_much_lower_than_set:
                setpoint_channel = [x for x in zones[zone] if 'set' in x][0]
                setpoints = channels[setpoint_channel]['values']
                times = channels[setpoint_channel]['times']
                last_setpoint = setpoints[-1]
                last_setpoint_time = times[-1]

                # No thermostat change: alert immediately
                if len(set(channels[setpoint_channel]['values'])) == 1:
                    print('[ALERT] Not caused by a thermostat change!')
                    send_opsgenie_alert(
                        house_alias,
                        setpoint_channel.replace('-set',''),
                    )
                else:
                    # Find the latest thermostat increase
                    lower_setpoints = [(t,s) for t,s in zip(times,setpoints) if s<last_setpoint]
                    if lower_setpoints:
                        last_lower_setpoints = lower_setpoints[-1]
                        time_increased = pendulum.from_timestamp(last_lower_setpoints[0]/1000)
                        time_since_increased = round((last_setpoint_time - last_lower_setpoints[0])/1000/60)
                        # Warn that the setpoit has not been reached yet
                        if time_since_increased > 2*RUN_EVERY_MIN and zone not in warnings[house_alias]:
                            print(f"[Warning] Setpoint in {zone} increased at {time_increased}, and has not been reached yet")
                            # send_opsgenie_warning(
                            #     f"[{house_alias}] Setpoint in {zone} increased at {time_increased}, and has not been reached yet."
                            # )
                            warnings[house_alias][zone] = True
                    # There was no increase in thermostat: alert immediately
                    else:
                        print('[ALERT] Not caused by a thermostat increase!')
                        send_opsgenie_alert(
                            house_alias,
                            setpoint_channel.replace('-set',''),
                        )


if __name__ == "__main__":
    while True:
        check_setpoint()
        time.sleep(RUN_EVERY_MIN * 60)
