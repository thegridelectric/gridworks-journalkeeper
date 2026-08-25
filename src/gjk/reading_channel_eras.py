"""Which reading_channels row a reading belongs to, by time.

A `(terminal_asset_alias, name)` can carry several rows over its life: one
active (`deactivated_date IS NULL`) and any number of retired ones, each
ending at its `deactivated_date`. Rows carry no start date, so an era is
identified only by its end: the row whose era contains a time `t` is the one
with the earliest `deactivated_date` after `t`, and the active row when no
retired row ends after `t`.

Live JournalKeeper only ever needs the active row. The S3 back-fill needs
the era rows because a channel's definition — its unit — can change across
layouts under the same name (`buffer-depth1`: `WaterTempCTimes1000` data
channel through 2025, `FahrenheitX100` derived channel from 2026), and the
front end reads `reading_channels.unit` to scale what it plots.
"""

import uuid
from datetime import datetime

from gw_data.db.models import ReadingChannelSql
from sqlalchemy.orm import Session


def load_channel_rows(
    db: Session, terminal_asset_alias: str
) -> list[ReadingChannelSql]:
    """Every row (active and retired) for the terminal asset."""
    return (
        db
        .query(ReadingChannelSql)
        .filter(ReadingChannelSql.terminal_asset_alias == terminal_asset_alias)
        .all()
    )


def channel_ids_at(rows: list[ReadingChannelSql], t: datetime) -> dict[str, uuid.UUID]:
    """Map channel name -> id of the row whose era contains `t`."""
    by_name: dict[str, list[ReadingChannelSql]] = {}
    for r in rows:
        by_name.setdefault(r.name, []).append(r)
    result: dict[str, uuid.UUID] = {}
    for name, candidates in by_name.items():
        retired_after_t = sorted(
            (
                r
                for r in candidates
                if r.deactivated_date is not None and r.deactivated_date > t
            ),
            key=lambda r: r.deactivated_date,
        )
        if retired_after_t:
            result[name] = retired_after_t[0].id
            continue
        active = [r for r in candidates if r.deactivated_date is None]
        if active:
            result[name] = active[0].id
    return result
