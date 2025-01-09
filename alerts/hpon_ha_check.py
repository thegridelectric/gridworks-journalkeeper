import json
import time

import dotenv
import pendulum
import requests
from gjk.api_db import get_db
from gjk.config import Settings
from gjk.models import MessageSql
from sqlalchemy import asc, or_
from sqlalchemy.exc import SQLAlchemyError

GRIDWORKS_DEV_OPS_GENIE_TEAM_ID = "edaccf48-a7c9-40b7-858a-7822c6f862a4"
RUN_EVERY_MIN = 10
MIN_GPM_TIMES_100 = 0.5*100
MIN_POWER_KW = 1

alerts = {}
settings = Settings(_env_file=dotenv.find_dotenv())


def send_opsgenie_alert(house_alias):
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]
    payload = {
        "message": f"[{house_alias}] HP is not on even though HA state says HpOn",
        "alias": f"{pendulum.now(tz='America/New_York').format('YYYY-MM-DD')}--{house_alias}-hpnoton",
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


def check_hp_on():
    global alerts

    try:
        # Use the get_db generator to create a new session
        with next(get_db()) as session:
            # Get the data
            start_ms = pendulum.now(tz="America/New_York").add(hours=-4).timestamp() * 1000
            end_ms = pendulum.now(tz="America/New_York").add(hours=-3).timestamp() * 1000
            messages = (
                session.query(MessageSql)
                .filter(
                    or_(
                        MessageSql.message_type_name == "batched.readings",
                        MessageSql.message_type_name == "report",
                    ),
                    MessageSql.message_persisted_ms >= start_ms,
                    MessageSql.message_persisted_ms <= end_ms,
                )
                .order_by(asc(MessageSql.message_persisted_ms))
                .all()
            )

            if not messages:
                print("No messages found.")
                return

            # For every house
            all_house_aliases = list({
                x.from_alias for x in messages if "orange" not in x.from_alias
            })
            all_house_aliases = [x.split(".")[-2] for x in all_house_aliases]
            for house_alias in all_house_aliases:
                print(f"\n{house_alias}\n")
                if house_alias not in alerts:
                    alerts[house_alias] = False
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
                        if "hp" in channel_name: 
                            if channel_name not in channels:
                                channels[channel_name] = {
                                    "values": channel["ValueList"],
                                    "times": channel["ScadaReadTimeUnixMsList"],
                                }
                            else:
                                channels[channel_name]["values"].extend(
                                    channel["ValueList"]
                                )
                                channels[channel_name]["times"].extend(
                                    channel["ScadaReadTimeUnixMsList"]
                                )
                if "hp-idu-pwr" and "hp-odu-pwr" not in channels:
                    return
                # Sort according to time
                for key in channels.keys():
                    sorted_times_values = sorted(
                        zip(channels[key]["times"], channels[key]["values"])
                    )
                    sorted_times, sorted_values = zip(*sorted_times_values)
                    channels[key]["values"] = list(sorted_values)
                    channels[key]["times"] = list(sorted_times)

                # RELAY 5
                minutes_since_scada_in_ctrl = 0
                relay_5 = {}
                for message in [m for m in messages if house_alias in m.from_alias]:
                    if 'StateList' in message.payload:
                        for state in message.payload['StateList']:
                            if 'relay5' in state['MachineHandle']:
                                if state['MachineHandle'] not in relay_5:
                                    relay_5[state['MachineHandle']] = {}
                                    relay_5[state['MachineHandle']]['times'] = []
                                    relay_5[state['MachineHandle']]['values'] = []
                                relay_5[state['MachineHandle']]['times'].extend(state['UnixMsList'])
                                relay_5[state['MachineHandle']]['values'].extend(state['StateList'])
                most_recent_relay5_parent = list(relay_5.keys())[0]
                if len(list(relay_5.keys()))>1:
                    most_recent_relay_state = pendulum.datetime(2022,1,1).timestamp()*1000
                    for r in relay_5:
                        latest = max(relay_5[r]['times'])
                        if latest > most_recent_relay_state:
                            most_recent_relay_state = latest
                            most_recent_relay5_parent = r
                    print(f"The most recent actor to control relays 5 is {most_recent_relay5_parent}")
                for r in relay_5:
                    if r!= most_recent_relay5_parent:
                        continue
                    pairs = list(zip(relay_5[r]['times'], relay_5[r]['values']))
                    time_of_last_switch = next(
                        (
                            pairs[i + 1][0]
                            for i in range(len(pairs) - 2, -1, -1)
                            if pairs[i][1] != pairs[i + 1][1]
                        ),
                        pairs[0][0],
                    )
                    time_of_last_switch = pendulum.from_timestamp(
                        time_of_last_switch / 1000, tz="America/New_York"
                    )
                    print(
                        f"In {relay_5[r]['values'][-1]} since {time_of_last_switch}"
                    )
                    # If it has been more than 10 minutes since the relay is Closed
                    if relay_5[r]["values"][-1] == "Scada":
                        if (pendulum.now(tz="America/New_York") - time_of_last_switch).total_seconds() > 10 * 60:
                            minutes_since_scada_in_ctrl = pendulum.now(tz='America/New_York').diff(time_of_last_switch).in_minutes()
                            print(f"Condition 1: Scada in control since {minutes_since_scada_in_ctrl} minutes")
                
                # RELAY 6
                minutes_since_hp_on = 0
                relay_6 = {}
                for message in [m for m in messages if house_alias in m.from_alias]:
                    if 'StateList' in message.payload:
                        for state in message.payload['StateList']:
                            if 'relay6' in state['MachineHandle']:
                                if state['MachineHandle'] not in relay_6:
                                    relay_6[state['MachineHandle']] = {}
                                    relay_6[state['MachineHandle']]['times'] = []
                                    relay_6[state['MachineHandle']]['values'] = []
                                relay_6[state['MachineHandle']]['times'].extend(state['UnixMsList'])
                                relay_6[state['MachineHandle']]['values'].extend(state['StateList'])
                most_recent_relay6_parent = list(relay_6.keys())[0]
                if len(list(relay_6.keys()))>1:
                    most_recent_relay_state = pendulum.datetime(2022,1,1).timestamp()*1000
                    for r in relay_6:
                        latest = max(relay_6[r]['times'])
                        if latest > most_recent_relay_state:
                            most_recent_relay_state = latest
                            most_recent_relay6_parent = r
                    print(f"The most recent actor to control relays 5 is {most_recent_relay6_parent}")
                for r in relay_6:
                    if r!= most_recent_relay6_parent:
                        continue
                    pairs = list(zip(relay_6[r]['times'], relay_6[r]['values']))
                    time_of_last_switch = next(
                        (
                            pairs[i + 1][0]
                            for i in range(len(pairs) - 2, -1, -1)
                            if pairs[i][1] != pairs[i + 1][1]
                        ),
                        pairs[0][0],
                    )
                    time_of_last_switch = pendulum.from_timestamp(
                        time_of_last_switch / 1000, tz="America/New_York"
                    )
                    print(
                        f"In {relay_6[r]['values'][-1]} since {time_of_last_switch}"
                    )
                    # If it has been more than 10 minutes since the relay is Closed
                    if relay_6[r]["values"][-1] == "RelayClosed":
                        if (pendulum.now(tz="America/New_York") - time_of_last_switch).total_seconds() > 10 * 60:
                            minutes_since_hp_on = pendulum.now(tz='America/New_York').diff(time_of_last_switch).in_minutes()
                            print(f"Condition 2: RelayClosed (HP on) since {minutes_since_hp_on} minutes")

                if minutes_since_scada_in_ctrl>10 and minutes_since_hp_on>10:
                    print("HP SHOULD BE ON!")
                    hp_should_be_on = True
                else:
                    print("HP should not be on.")
                    hp_should_be_on = False
                    alerts[house_alias] = False

                if hp_should_be_on:
                    # Find all times where the HP was on
                    if "hp-odu-pwr" in channels:
                        times = channels["hp-odu-pwr"]["times"]
                        values = [x / 1000 for x in channels["hp-odu-pwr"]["values"]]
                        on_times_odu = [
                            t for t, v in zip(times, values) if v >= MIN_POWER_KW
                        ]
                    else:
                        on_times_odu = []
                    if "hp-idu-pwr" in channels:
                        times = channels["hp-idu-pwr"]["times"]
                        values = [x / 1000 for x in channels["hp-idu-pwr"]["values"]]
                        on_times_idu = [
                            t for t, v in zip(times, values) if v >= MIN_POWER_KW
                        ]
                    else:
                        on_times_idu = []
                    on_times = sorted(on_times_odu + on_times_idu)

                    # Check if any of them was in the last 5 min
                    hp_came_on = False
                    for time_ms in on_times:
                        if time.time() - time_ms/1000 < 5*60:
                            hp_came_on = True
                    if hp_came_on:
                        print("[OK] The HP was on at some point in the last 5min")
                        alerts[house_alias] = False
                    elif not alerts[house_alias]:
                        print("[ALERT] The HP did not come on!")
                        send_opsgenie_alert(house_alias)
                        alerts[house_alias] = True


    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    while True:
        check_hp_on()
        time.sleep(RUN_EVERY_MIN * 60)
