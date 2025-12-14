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
MAX_TEMP_F = 170
warnings = {}
alert_sent = {}
settings = Settings(_env_file=dotenv.find_dotenv())


def to_fahrenheit(t):
    return t * 9 / 5 + 32


def send_opsgenie_alert(house_alias, message):
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]
    payload = {
        "message": message,
        "alias": f"{pendulum.now(tz='America/New_York').format('YYYY-MM-DD')}--{house_alias}-hottemps",
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


def check_hot_temps():
    global warnings

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
            all_house_aliases = list({x.from_alias for x in messages})
            all_house_aliases = [x.split(".")[-2] for x in all_house_aliases]
            for house_alias in all_house_aliases:
                if house_alias != "beech":
                    continue
                print(f"\n{house_alias}\n")
                if house_alias not in warnings:
                    warnings[house_alias] = {}
                if house_alias not in alert_sent:
                    alert_sent[house_alias] = False
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
                        if (
                            "buffer-depth" in channel_name
                            and "micro" not in channel_name
                        ) or (
                            "tank" in channel_name
                            and "depth" in channel_name
                            and "micro" not in channel_name
                        ):
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

                # Check for too hot temperatures
                for channel in channels.keys():
                    latest_temp = to_fahrenheit(channels[channel]["values"][-1] / 1000)
                    print(f"{channel} - {round(latest_temp, 1)}")
                    if latest_temp > MAX_TEMP_F and not alert_sent[house_alias]:
                        print(
                            f"[ALERT] {channel} is hotter than {MAX_TEMP_F} F ({round(latest_temp, 1)})"
                        )
                        msg = f"[{house_alias}] {channel} is hotter than {MAX_TEMP_F} F"
                        send_opsgenie_alert(house_alias, msg)

    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    while True:
        check_hot_temps()
        time.sleep(RUN_EVERY_MIN * 60)
