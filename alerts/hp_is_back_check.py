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
MIN_POWER_KW = 0.006
RUN_EVERY_MIN = 5
warnings = {}
alert_sent = {}

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()


def send_opsgenie_alert(house_alias):
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]
    payload = {
        "message": f"[{house_alias}] The HP is back!",
        "alias": f"{pendulum.now(tz='America/New_York').format('YYYY-MM-DD')}--{house_alias}-hpisback",
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


def check_hpback():
    global warnings

    # Get the data
    start_ms = pendulum.now(tz="America/New_York").add(hours=-1).timestamp() * 1000
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
    all_house_aliases = ['fir'] # just for fir
    for house_alias in all_house_aliases:
        print(f"\n{house_alias}\n")
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
                if "hp" in channel_name:
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

        # Find all times where the HP was on
        if "hp-odu-pwr" in channels:
            times = channels["hp-odu-pwr"]["times"]
            values = [x / 1000 for x in channels["hp-odu-pwr"]["values"]]
            print(f'Max ODU power: {max(values)}')
            on_times_odu = [t for t, v in zip(times, values) if v >= MIN_POWER_KW]
        else:
            on_times_odu = []
        if "hp-idu-pwr" in channels:
            times = channels["hp-idu-pwr"]["times"]
            values = [x / 1000 for x in channels["hp-idu-pwr"]["values"]]
            print(f'Max IDU power: {max(values)}')
            on_times_idu = [t for t, v in zip(times, values) if v >= MIN_POWER_KW]
        else:
            on_times_idu = []
        on_times = sorted(on_times_odu + on_times_idu)

        # Check if any of them was on during onpeak
        if on_times and not alert_sent[house_alias]:
            send_opsgenie_alert(house_alias)
            print('Its back!')
            alert_sent[house_alias] = True
        else:
            print("Still waiting for power to the HP")


if __name__ == "__main__":
    while True:
        check_hpback()
        time.sleep(RUN_EVERY_MIN * 60)
