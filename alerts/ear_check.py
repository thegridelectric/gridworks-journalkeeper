import json
import subprocess
import time
import dotenv
import pendulum
import requests
from gjk.config import Settings

GRIDWORKS_DEV_OPS_GENIE_TEAM_ID = "edaccf48-a7c9-40b7-858a-7822c6f862a4"


def latest_messages() -> list[str]:
    # Get the current date in UTC
    current_date = pendulum.now("UTC").format("YYYYMMDD")
    # Define the S3 bucket and path, replacing the date with the current UTC date
    bucket = "s3://gwdev/hw1__1/eventstore/"
    path = f"{bucket}{current_date}/"
    # Time window to check (10 minutes ago)
    ten_minutes_ago = pendulum.now("UTC").subtract(minutes=10)
    try:
        # Execute AWS CLI command to list files in the S3 path
        result = subprocess.run(
            ["aws", "s3", "ls", path], capture_output=True, text=True, check=True
        )
        files = result.stdout.splitlines()
        recent_files = []
        # Loop through the files and check their timestamps
        for file in files:
            file_name = file.split()[-1]
            try:
                # Extract the timestamp from the file name (milliseconds part)
                milliseconds_part = int(file_name.split("-")[2])
                persisted_time = pendulum.from_timestamp(
                    milliseconds_part / 1000, tz="UTC"
                )
                # Check if the file was uploaded in the last 10 minutes
                if persisted_time >= ten_minutes_ago:
                    recent_files.append(file_name)
            except (IndexError, ValueError):
                print(f"Could not process file: {file_name}")
        print(f"{len(recent_files)} files uploaded in the last 10 minutes.")
    except subprocess.CalledProcessError as e:
        print(f"Error running AWS CLI command: {e}")
    return len(recent_files)


def send_opsgenie_alert(settings: Settings):
    # Create OpsGenie client configuration
    url = "https://api.opsgenie.com/v2/alerts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {settings.ops_genie_api_key.get_secret_value()}",
    }
    responders = [{"type": "team", "id": GRIDWORKS_DEV_OPS_GENIE_TEAM_ID}]

    payload = {
        "message": "No Messages to S3! Check the ear.",
        "alias": "s3-flatlined",
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


if __name__ == "__main__":
    from datetime import datetime
    with open("/home/ubuntu/gridworks-journalkeeper/alerts/ear_check.log", "a") as log_file:
        log_file.write(f"Script executed at: {datetime.now()}\n")

    while(True):
        print("Searching for latest messages...")
        settings = Settings(_env_file=dotenv.find_dotenv())
        num_messages = latest_messages()
        if num_messages == 0:
            send_opsgenie_alert(settings)
        time.sleep(10*60)