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
MIN_GPM_TIMES_100 = 0.5 * 100
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
        "message": f"[{house_alias}] ATN is not running",
        "alias": f"{pendulum.now(tz='America/New_York').format('YYYY-MM-DD')}--{house_alias}-not_atn",
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
            start_ms = (
                pendulum.now(tz="America/New_York").add(hours=-1).timestamp() * 1000
            )
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
                print("No messages found.")
                return

            # For every house
            all_house_aliases = list({
                x.from_alias
                for x in messages
                if "oak" in x.from_alias or "beech" in x.from_alias
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
                # Sort according to time
                for key in channels.keys():
                    sorted_times_values = sorted(
                        zip(channels[key]["times"], channels[key]["values"])
                    )
                    sorted_times, sorted_values = zip(*sorted_times_values)
                    channels[key]["values"] = list(sorted_values)
                    channels[key]["times"] = list(sorted_times)

                # RELAY 5
                relay_5 = {}
                for message in [m for m in messages if house_alias in m.from_alias]:
                    if "StateList" in message.payload:
                        for state in message.payload["StateList"]:
                            if "relay5" in state["MachineHandle"]:
                                if state["MachineHandle"] not in relay_5:
                                    relay_5[state["MachineHandle"]] = {}
                                    relay_5[state["MachineHandle"]]["times"] = []
                                    relay_5[state["MachineHandle"]]["values"] = []
                                relay_5[state["MachineHandle"]]["times"].extend(
                                    state["UnixMsList"]
                                )
                                relay_5[state["MachineHandle"]]["values"].extend(
                                    state["StateList"]
                                )
                most_recent_relay5_parent = list(relay_5.keys())[0]
                if len(list(relay_5.keys())) > 1:
                    most_recent_relay_state = (
                        pendulum.datetime(2022, 1, 1).timestamp() * 1000
                    )
                    for r in relay_5:
                        latest = max(relay_5[r]["times"])
                        if latest > most_recent_relay_state:
                            most_recent_relay_state = latest
                            most_recent_relay5_parent = r
                print(f"The most recent actor to control relays 5 is {most_recent_relay5_parent}")
            
                if most_recent_relay5_parent == 'a.aa.relay5':
                    print("[OK] Atomic Ally is in control")
                    alerts[house_alias] = False
                elif not alerts[house_alias] == 'auto.h.n.relay5':
                    print("[ALERT] In HomeAlone!")
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
