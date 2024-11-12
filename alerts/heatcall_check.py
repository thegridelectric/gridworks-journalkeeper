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
MIN_POWER_KW = 2
MAX_WARNINGS = 3
RUN_EVERY_MIN = 10
warnings = {}

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()


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

    # Get the data
    start_ms = pendulum.now(tz="America/New_York").add(days=-1).timestamp() * 1000
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
                if ("zone" in channel_name and "state" in channel_name) or (
                    channel_name == "dist-pump-pwr"
                ):
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

        # Find the last heat call in the house
        last_heatcall_time = 0
        for zone in [
            channels[channel] for channel in channels.keys() if "zone" in channel
        ]:
            last_heatcall_zone = [
                zone["times"][i]
                for i in range(len(zone["times"]))
                if zone["values"][i] == 1
            ]
            if last_heatcall_zone:
                last_heatcall_time = max(last_heatcall_zone[-1], last_heatcall_time)
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
                        if flow["times"][i] <= last_heatcall_time - 5 * 60 * 1000
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
        else:
            print("Last heat call was more than 24 hours ago.")

        # Send Opsgenie alert if there have been too many warnings
        if len(warnings[house_alias]) == MAX_WARNINGS:
            print(f"[ALERT] There are 3 unsatisfied heat calls at {house_alias}!")
            send_opsgenie_alert(
                house_alias,
                pendulum.from_timestamp(
                    last_heatcall_time / 1000, tz="America/New_York"
                ),
            )

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


if __name__ == "__main__":
    while True:
        check_distflow()
        time.sleep(RUN_EVERY_MIN * 60)
