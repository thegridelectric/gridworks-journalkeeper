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
MIN_POWER_KW = 2
MIN_FLOW_GPM = 0.5
MAX_WARNINGS = 3
RUN_EVERY_MIN = 10
warnings = {}
settings = Settings(_env_file=dotenv.find_dotenv())


def send_opsgenie_alert(house_alias, heat_call_time):
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]
    payload = {
        "message": f"[{house_alias}] No dist-flow has been recorded after a heat call at {heat_call_time}.",
        "alias": f"{pendulum.now(tz='America/New_York').format('YYYY-MM-DD')}--{house_alias}-distflow",
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


def check_distflow():
    global warnings

    try:
        # Use the get_db generator to create a new session
        with next(get_db()) as session:
            # Get the data
            start_ms = (
                pendulum.now(tz="America/New_York").add(days=-1).timestamp() * 1000
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
                print(f"\n{house_alias}\n")
                if house_alias not in warnings:
                    warnings[house_alias] = []
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
                        if (("zone" in channel_name and "state" in channel_name) 
                            or (channel_name == "dist-pump-pwr") 
                            or (channel_name == "dist-flow")):
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

                # Find the last heat call in the house
                last_heatcall_time = 0
                for zone in [
                    channels[channel]
                    for channel in channels.keys()
                    if "zone" in channel
                ]:
                    last_heatcall_zone = [
                        zone["times"][i]
                        for i in range(len(zone["times"]))
                        if zone["values"][i] == 1
                    ]
                    if last_heatcall_zone:
                        last_heatcall_time = max(
                            last_heatcall_zone[-1], last_heatcall_time
                        )
                if last_heatcall_time > 0:
                    print(
                        f"Last heat call at {pendulum.from_timestamp(last_heatcall_time / 1000, tz='America/New_York')}"
                    )

                    # Try to find flow data around the last heat call
                    for flow in [
                        channels[channel]
                        for channel in channels.keys()
                        if "dist-pump-pwr" in channel
                    ]:
                        flow_around_heatcall = [
                            flow["values"][i]
                            for i in range(len(flow["times"]))
                            if flow["times"][i] >= last_heatcall_time - 5 * 60 * 1000
                        ]
                        if not flow_around_heatcall:
                            # Check the last value before heatcall-5min
                            last_flow_before_hc5 = [
                                flow["values"][i]
                                for i in range(len(flow["times"]))
                                if flow["times"][i]
                                <= last_heatcall_time - 5 * 60 * 1000
                            ]
                            if last_flow_before_hc5:
                                # The dist pump was off
                                if last_flow_before_hc5[-1] <= MIN_POWER_KW:
                                    if last_heatcall_time not in warnings[house_alias]:
                                        warnings[house_alias].append(last_heatcall_time)
                                        print(
                                            f"[WARNING {len(warnings[house_alias])}/{MAX_WARNINGS}] Distribution pump has not reported any activity during or after that heat call."
                                        )
                            elif last_heatcall_time not in warnings[house_alias]:
                                warnings[house_alias].append(last_heatcall_time)
                                print(
                                    f"[WARNING {len(warnings[house_alias])}/{MAX_WARNINGS}] Distribution pump has not reported any activity during or after that heat call."
                                )
                        elif max(flow_around_heatcall) <= MIN_POWER_KW:
                            if last_heatcall_time not in warnings[house_alias]:
                                warnings[house_alias].append(last_heatcall_time)
                                print(
                                    f"[WARNING {len(warnings[house_alias])}/{MAX_WARNINGS}] Distribution pump has not reported any activity during or after that heat call."
                                )
                        # Reset the warnings if there was flow around the last heat call
                        else:
                            print(
                                "[OK] Distribution pump came on during or after that heat call."
                            )
                            warnings[house_alias] = []
                    # Try the same with flow
                    for flow in [
                        channels[channel]
                        for channel in channels.keys()
                        if "dist-flow" in channel
                    ]:
                        flow_around_heatcall = [
                            flow["values"][i]
                            for i in range(len(flow["times"]))
                            if flow["times"][i] >= last_heatcall_time - 5 * 60 * 1000
                        ]
                        # Reset the warnings if there was flow around the last heat call
                        if flow_around_heatcall:
                            print(f"Max flow: {max(flow_around_heatcall)/100} GPM")
                        if flow_around_heatcall and max(flow_around_heatcall) >= MIN_FLOW_GPM*100:
                            print(
                                "[OK] Distribution pump came on during or after that heat call."
                            )
                            warnings[house_alias] = []
                else:
                    print("Last heat call was more than 24 hours ago.")

                # Send Opsgenie alert if there have been too many warnings
                if len(warnings[house_alias]) == MAX_WARNINGS:
                    print(
                        f"[ALERT] There are 3 unsatisfied heat calls at {house_alias}!"
                    )
                    send_opsgenie_alert(
                        house_alias,
                        pendulum.from_timestamp(
                            last_heatcall_time / 1000, tz="America/New_York"
                        ),
                    )

                print(f"Done for {house_alias}.")

    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    while True:
        check_distflow()
        time.sleep(RUN_EVERY_MIN * 60)
