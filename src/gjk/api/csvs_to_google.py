# From https://github.com/thegridelectric/gridworks-journalkeeper/blob/dev/src/gjk/api/csvs_to_google.py
import time

import pendulum
import requests

short_aliases = ["oak", "beech", "fir"]

URL = "http://journalmaker.electricity.works:8000/latest-scada-report"
INTERVAL = 300  # 5 minutes in seconds
OUT_STUB = "/home/ubuntu/gdrive/MillinocketData/ScadaReportA"


def fetch_and_save_csv():
    for short_alias in short_aliases:
        try:
            url = f"{URL}/{short_alias}"
            response = requests.get(url)
            response.raise_for_status()
            content_disposition = response.headers.get("Content-Disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            else:
                # Fallback to generating a filename if not provided
                timestamp = pendulum.now("America/New_York").format("YYYYMMDD")
                filename = f"{short_alias}_{timestamp}.csv"
            with open(filename, "w") as f:
                f.write(response.text)
            print(f"CSV saved as {filename}")
        except requests.RequestException as e:
            print(f"Error fetching CSV: {e}")


def main():
    while True:
        fetch_and_save_csv()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
