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
MIN_POWER_W = 5
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
        "message": f"[{house_alias}] Store flow is zero even though relay 9 is closed",
        "alias": f"{pendulum.now(tz='America/New_York').format('YYYY-MM-DD')}--{house_alias}-storeflow",
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


def check_storeflow():
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
                        if channel_name == "store-pump-pwr" or channel_name == "store-flow":
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
                if "store-pump-pwr" in channels:
                    # Sort according to time
                    for key in channels.keys():
                        sorted_times_values = sorted(
                            zip(channels[key]["times"], channels[key]["values"])
                        )
                        sorted_times, sorted_values = zip(*sorted_times_values)
                        channels[key]["values"] = list(sorted_values)
                        channels[key]["times"] = list(sorted_times)

                    # Position of relay 9
                    relays = {}
                    for message in [m for m in messages if house_alias in m.from_alias]:
                        if 'StateList' in message.payload:
                            for state in message.payload['StateList']:
                                if 'relay9' in state['MachineHandle']:
                                    if state['MachineHandle'] not in relays:
                                        relays[state['MachineHandle']] = {}
                                        relays[state['MachineHandle']]['times'] = []
                                        relays[state['MachineHandle']]['values'] = []
                                    relays[state['MachineHandle']]['times'].extend(state['UnixMsList'])
                                    relays[state['MachineHandle']]['values'].extend(state['StateList'])

                    # Keep only the latest actor in control
                    most_recent_relay9_parent = list(relays.keys())[0]
                    if len(list(relays.keys()))>1:
                        most_recent_relay_state = pendulum.datetime(2022,1,1).timestamp()*1000
                        for r in relays:
                            latest = max(relays[r]['times'])
                            if latest > most_recent_relay_state:
                                most_recent_relay_state = latest
                                most_recent_relay9_parent = r
                        print(f"The most recent actor to control relay 9 is {most_recent_relay9_parent}")

                    for r in relays:
                        if r!= most_recent_relay9_parent:
                            continue
                        pairs = list(zip(relays[r]['times'], relays[r]['values']))
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
                            f"In {relays[r]['values'][-1]} since {time_of_last_switch}"
                        )

                        # If it has been more than 10 minutes since the relay is Closed
                        # There must have been flow on the storage pump
                        if relays[r]["values"][-1] == "RelayClosed":
                            if (
                                pendulum.now(tz="America/New_York")
                                - time_of_last_switch
                            ).total_seconds() > 10 * 60:
                                print(
                                    f"Its been {pendulum.now(tz='America/New_York').diff(time_of_last_switch).in_minutes()}min"
                                )

                                store_flow_since_switch = sum([
                                    y if y > MIN_POWER_W else 0
                                    for x, y in zip(
                                        channels["store-pump-pwr"]["times"],
                                        channels["store-pump-pwr"]["values"],
                                    )
                                    if x / 1000 >= time_of_last_switch.timestamp()
                                ])

                                if store_flow_since_switch < 2*MIN_POWER_W and "store-flow" in channels:
                                    store_flow_since_switch = sum([
                                        y if y > MIN_GPM_TIMES_100 else 0
                                        for x, y in zip(
                                            channels["store-flow"]["times"],
                                            channels["store-flow"]["values"],
                                        )
                                        if x / 1000 >= time_of_last_switch.timestamp()
                                    ])

                                if (
                                    store_flow_since_switch < 2*MIN_GPM_TIMES_100
                                    and not alerts[house_alias]
                                ):
                                    print("ALERT: no store flow")
                                    alerts[house_alias] = True
                                    send_opsgenie_alert(house_alias)

                                if store_flow_since_switch > 0:
                                    print("The store pump came on")
                                    alerts[house_alias] = False

    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    while True:
        check_storeflow()
        time.sleep(RUN_EVERY_MIN * 60)
