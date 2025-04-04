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
ON_PEAK_HOURS = [7, 8, 9, 10, 11] + [16, 17, 18, 19]
MIN_POWER_KW = 1
RUN_EVERY_MIN = 2
MAX_SECONDS_SINCE_LAST_SNAPSHOT = 70
warnings = {}
alert_sent = {}
settings = Settings(_env_file=dotenv.find_dotenv())


def send_opsgenie_alert(house_alias):
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]
    payload = {
        "message": f"[{house_alias}] Not receiving snapshots every 30 seconds!",
        "alias": f"{pendulum.now(tz='America/New_York').format('YYYY-MM-DD')}--{house_alias}-nosnapshots",
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


def check_heartbeat():
    global warnings

    try:
        # Use the get_db generator to create a new session
        with next(get_db()) as session:
            start_ms = pendulum.now(tz="America/New_York").add(minutes=-3).timestamp() * 1000
            snapshots = session.query(MessageSql).filter(
                MessageSql.message_type_name == "snapshot.spaceheat",
                MessageSql.message_persisted_ms >= start_ms,
            ).order_by(asc(MessageSql.message_persisted_ms)).all()

            all_house_aliases = list({x.from_alias for x in snapshots})
            all_house_aliases = [
                alias for alias in all_house_aliases if alias.split(".")[0] == "hw1"
            ]
            all_house_aliases = [x.split(".")[-2] for x in all_house_aliases]
            for house_alias in all_house_aliases:
                print(f"\n{house_alias}\n")
                if house_alias not in warnings:
                    warnings[house_alias] = {}
                if house_alias not in alert_sent:
                    alert_sent[house_alias] = False

                if not snapshots:
                    print("No snapshots found!")
                    most_recent = start_ms
                else:
                    most_recent = max(snapshots, key= lambda x: x.message_persisted_ms).message_persisted_ms

                # print(f"Most recent: {pendulum.from_timestamp(most_recent / 1000, tz='America/New_York')}")
                print(f"Most recent was {round(time.time() - most_recent/1000,1)} seconds ago")

                if time.time() - most_recent/1000 > MAX_SECONDS_SINCE_LAST_SNAPSHOT:
                    if not alert_sent[house_alias]:
                        print("ALERT")
                        send_opsgenie_alert(house_alias)
                        alert_sent[house_alias] = True
                elif alert_sent[house_alias]:
                    alert_sent[house_alias] = False

    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    while True:
        check_heartbeat()
        time.sleep(RUN_EVERY_MIN * 60)
