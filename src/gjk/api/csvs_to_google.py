# From https://github.com/thegridelectric/gridworks-journalkeeper/blob/dev/src/gjk/api/csvs_to_google.py

import time
import pendulum
import requests

short_aliases = ["oak", "beech", "fir"]

URL = "http://journalmaker.electricity.works:8000/scada-report" # 5 minutes in seconds
OUT_STUB = "/home/ubuntu/gdrive/MillinocketData/ScadaReportB"
TZ_STRING = "America/New_York"


def fetch_and_save_csv():
    previous_day = pendulum.now(TZ_STRING).subtract(days=1)
    date_str = previous_day.format("YYYYMMDD")
    print(f"Fetching data for date: {date_str}")
    for short_alias in short_aliases:
        try:
            url = f"{URL}/{short_alias}/{date_str}"
            response = requests.get(url)
            response.raise_for_status()
            content_disposition = response.headers.get("Content-Disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            else:
                # Fallback to generating a filename if not provided
                timestamp = pendulum.now("America/New_York").format("YYYYMMDD")
                filename = f"{short_alias}_{timestamp}.csv"
            file_path = f"{OUT_STUB}/{filename}"
            with open(file_path, "w") as f:
                f.write(response.text)
            print(f"CSV saved as {filename}")
        except requests.RequestException as e:
            print(f"Error fetching CSV: {e}")
        time.sleep(300)
    now = pendulum.now(TZ_STRING)
    print(f"Task completed at {now.format('YYYY-MM-DD HH:mm:ss')} {TZ_STRING}")


def main():
    print(f"Script started. Will run daily after 00:10 {TZ_STRING}")
    task_complete = False

    while True:
        now = pendulum.now(TZ_STRING)

        # Check if it's past 00:10 and the task hasn't been completed today
        if now.time() > pendulum.time(0, 10) and not task_complete:
            print(f"Running task at {now.format('YYYY-MM-DD HH:mm:ss')} {TZ_STRING}")
            fetch_and_save_csv()
            task_complete = True

        # Reset task_complete at the start of a new day
        if now.time() <= pendulum.time(0, 0):
            task_complete = False

        time.sleep(60)


if __name__ == "__main__":
    main()
