import csv
from pathlib import Path
from typing import Dict, List

import pendulum
from fastapi import APIRouter, Depends, HTTPException
from fastapi.background import BackgroundTasks
from fastapi.responses import FileResponse
from gjk.api_db import get_db
from gjk.models import DataChannelSql, ReadingSql
from sqlalchemy import and_
from sqlalchemy.orm import Session

csv_maker_router = APIRouter()
TzString = "America/New_York"

# Global cache to store readings
readings_cache: Dict[str, List[ReadingSql]] = {}
last_update_time: Dict[str, pendulum.DateTime] = {}
today_str = ""


def update_cache(short_alias: str, db: Session) -> None:
    ny_tz = pendulum.timezone("America/New_York")
    now = pendulum.now(ny_tz)
    if short_alias not in last_update_time:
        # If it's the first update, get data for the whole day
        last_update_time[short_alias] = now.start_of("day")
    start_time = last_update_time[short_alias]
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)
    new_readings: List[ReadingSql] = (
        db.query(ReadingSql)
        .join(DataChannelSql)
        .filter(
            and_(
                DataChannelSql.terminal_asset_alias.like(f"%{short_alias}%"),
                ReadingSql.time_ms >= start_ms,
                ReadingSql.time_ms < end_ms,
            )
        )
        .order_by(DataChannelSql.name, ReadingSql.time_ms)
        .all()
    )
    print(f"Found {len(new_readings)} new readings for {short_alias}")
    if short_alias in readings_cache:
        # Append new readings to existing cache
        readings_cache[short_alias].extend(new_readings)
        # Sort and remove duplicates (if any)
        readings_cache[short_alias] = sorted(
            set(readings_cache[short_alias]),
            key=lambda r: (r.data_channel.name, r.time_ms),
        )
    else:
        readings_cache[short_alias] = new_readings
    last_update_time[short_alias] = now


def generate_csv(short_alias: str, db: Session) -> Path:
    global today_str
    ny_tz = pendulum.timezone(TzString)
    new_today_str = pendulum.now(ny_tz).start_of("day").format("YYYYMMDD")
    if new_today_str != today_str:
        readings_cache.clear()
        last_update_time.clear()
        today_str = new_today_str
    update_cache(short_alias, db)
    if short_alias not in readings_cache:
        raise HTTPException(
            status_code=404, detail=f"No readings found for {short_alias}"
        )
    readings: List[ReadingSql] = readings_cache[short_alias]
    ta_alias = readings[0].data_channel.terminal_asset_alias
    csv_file_path = Path(f"/tmp/{short_alias}_{today_str}.csv")
    with open(csv_file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["TerminalAsset", ta_alias])
        writer.writerow(["ReportTypeName", "scada.report.b.000"])
        writer.writerow([
            "Channel&Time",
            "LocalTime",
            "Channel",
            "TimeUnixMs",
            "Value",
            "TelemetryName",
        ])
        for r in readings:
            time_utc = pendulum.from_timestamp(r.time_ms / 1000, tz="America/New_York")
            writer.writerow([
                f"{r.data_channel.name}_{r.time_ms}",
                time_utc.format("YYYY-MM-DD HH:mm:ss"),
                r.data_channel.name,
                r.time_ms,
                r.value,
                r.data_channel.telemetry_name,
            ])
    return csv_file_path


@csv_maker_router.get("/latest-scada-report/{short_alias}")
def get_latest_scada_report(short_alias: str, db: Session = Depends(get_db)):
    try:
        csv_file_path = generate_csv(short_alias, db)
        background_tasks = BackgroundTasks()
        background_tasks.add_task(csv_file_path.unlink)

        return FileResponse(
            csv_file_path,
            media_type="text/csv",
            filename=f"{short_alias}_{today_str}.csv",
            background=background_tasks,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating CSV: {str(e)}"
        ) from e
