"""A house moving between two layouts that give one channel name two
telemetries, against real TimescaleDB, with real beech wire samples.

`dist-swt` is a WaterTempCTimes1000 data channel in the 2026 beech layout.
A later layout declares it as CelsiusTimes100 under a new channel Id, the
house goes back to the first layout, then forward again. The journal ends
with exactly two `dist-swt` rows, whose ids are the two layout Ids, each
reading on the row whose layout was in force at its time, and the row of
the layout in force at the end active. A last layout renames the channel
under the Celsius Id: a third row, with the Id as its `channel_id`.
"""

import json
import logging
import random
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from gw_data.db.models import ReadingChannelSql, ReadingSql
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

SAMPLES = Path(__file__).parent / "data" / "sample_messages" / "ops498"
BEECH = "hw1.isone.me.versant.keene.beech"
LAYOUT = "beech-layout.lite-011-2026-07-25.json"
REPORT = "beech-report.event-002-2026-07-25.json"
CHANNEL = "dist-swt"
RENAMED = "dist-swt-renamed"
HOUR_MS = 3_600_000

pytestmark = pytest.mark.integration


def _load(name: str, alias: str, shift_ms: int) -> dict:
    """A sample re-homed to `alias`: a fresh message id, channel Ids minted for
    the alias (a channel Id names one channel across the fleet), shifted in
    time."""
    payload = json.loads((SAMPLES / name).read_text().replace(BEECH, alias))
    seed = f"{alias}|{payload['MessageId']}|{shift_ms}"
    new_id = str(uuid.UUID(int=random.Random(seed).getrandbits(128), version=4))
    payload["MessageId"] = new_id
    for key in ("DataChannels", "DerivedChannels", "SynthChannels"):
        for channel in payload.get(key) or []:
            channel["Id"] = str(
                uuid.UUID(
                    int=random.Random(f"{alias}|{channel['Id']}").getrandbits(128),
                    version=4,
                )
            )
    if "Report" in payload:
        payload["Report"]["Id"] = new_id
        payload["TimeCreatedMs"] += shift_ms
        payload["Report"]["MessageCreatedMs"] += shift_ms
        for readings in payload["Report"]["ChannelReadingList"]:
            readings["ScadaReadTimeUnixMsList"] = [
                t + shift_ms for t in readings["ScadaReadTimeUnixMsList"]
            ]
        for states in payload["Report"]["StateList"]:
            states["UnixMsList"] = [t + shift_ms for t in states["UnixMsList"]]
    else:
        payload["MessageCreatedMs"] += shift_ms
    return payload


def _created_ms(payload: dict) -> int:
    return payload.get("MessageCreatedMs") or payload["TimeCreatedMs"]


def _with_celsius(layout: dict, channel_id: str) -> dict:
    """The layout with CHANNEL declared as CelsiusTimes100 under `channel_id`."""
    [channel] = [c for c in layout["DataChannels"] if c["Name"] == CHANNEL]
    channel["TelemetryName"] = "CelsiusTimes100"
    channel["Id"] = channel_id
    return layout


def _renamed(payload: dict, new_name: str) -> dict:
    """The layout or report with CHANNEL called `new_name`."""
    for channel in payload.get("DataChannels") or []:
        if channel["Name"] == CHANNEL:
            channel["Name"] = new_name
    for readings in payload.get("Report", {}).get("ChannelReadingList", []):
        if readings["ChannelName"] == CHANNEL:
            readings["ChannelName"] = new_name
    return payload


def _persist(persistor, payload: dict, alias: str):
    obj = persistor.codec.from_dict(payload, auto_upgrade=False)
    persistor.persist_message(
        f"{alias}.scada",
        datetime.fromtimestamp(_created_ms(payload) / 1000, UTC),
        obj,
        live=False,
    )


@pytest.fixture
def persistor(timescale_db_url):
    from gjk.config import Settings
    from gjk.sema import SemaCodec
    from gjk.sema_message_persistor import SemaMessagePersistor

    settings = Settings(db_url=SecretStr(timescale_db_url), service_alias="d1.journal")
    return SemaMessagePersistor(settings, SemaCodec(), logging.getLogger("test"))


@pytest.fixture
def db(timescale_db_url):
    engine = create_engine(timescale_db_url)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_toggling_layouts_reuses_the_two_rows_and_routes_by_layout_in_force(
    persistor, db
):
    alias = f"{BEECH}.toggle1"
    first = _load(LAYOUT, alias, 0)
    [channel] = [c for c in first["DataChannels"] if c["Name"] == CHANNEL]
    first_id = uuid.UUID(channel["Id"])
    second_id = uuid.uuid4()

    # Layouts at even hours, a report an hour after each.
    steps = [
        _load(LAYOUT, alias, 0 * HOUR_MS),
        _load(REPORT, alias, 1 * HOUR_MS),
        _with_celsius(_load(LAYOUT, alias, 2 * HOUR_MS), str(second_id)),
        _load(REPORT, alias, 3 * HOUR_MS),
        _load(LAYOUT, alias, 4 * HOUR_MS),
        _load(REPORT, alias, 5 * HOUR_MS),
        _with_celsius(_load(LAYOUT, alias, 6 * HOUR_MS), str(second_id)),
        _load(REPORT, alias, 7 * HOUR_MS),
        _renamed(_with_celsius(_load(LAYOUT, alias, 8 * HOUR_MS), str(second_id)), RENAMED),
        _renamed(_load(REPORT, alias, 9 * HOUR_MS), RENAMED),
    ]
    for payload in steps:
        _persist(persistor, payload, alias)
    db.expire_all()

    rows = (
        db
        .query(ReadingChannelSql)
        .filter(
            ReadingChannelSql.terminal_asset_alias == f"{alias}.ta",
            ReadingChannelSql.name.in_([CHANNEL, RENAMED]),
        )
        .all()
    )
    by_id = {r.id: r for r in rows}
    [renamed] = [r for r in rows if r.name == RENAMED]
    assert set(by_id) == {first_id, second_id, renamed.id}
    assert by_id[first_id].unit == "WaterTempCTimes1000"
    assert by_id[second_id].unit == "CelsiusTimes100"
    assert by_id[first_id].channel_id == first_id
    assert by_id[second_id].channel_id == second_id
    # the rename keeps the Celsius Id as its lineage under a surrogate key
    assert renamed.channel_id == second_id
    assert renamed.unit == "CelsiusTimes100"
    assert renamed.deactivated_date is None
    assert by_id[first_id].deactivated_date == datetime.fromtimestamp(
        _created_ms(steps[6]) / 1000, UTC
    )
    assert by_id[second_id].deactivated_date == datetime.fromtimestamp(
        _created_ms(steps[8]) / 1000, UTC
    )

    def reading_ms(channel_id: uuid.UUID) -> set[int]:
        return {
            int(r.timestamp.timestamp() * 1000)
            for r in db.query(ReadingSql).filter(ReadingSql.channel_id == channel_id)
        }

    def sample_ms(step: int) -> set[int]:
        [readings] = [
            c
            for c in steps[step]["Report"]["ChannelReadingList"]
            if c["ChannelName"] in (CHANNEL, RENAMED)
        ]
        return set(readings["ScadaReadTimeUnixMsList"])

    assert reading_ms(first_id) == sample_ms(1) | sample_ms(5)
    assert reading_ms(second_id) == sample_ms(3) | sample_ms(7)
    assert reading_ms(renamed.id) == sample_ms(9)
    report_persistor = persistor.custom_persistor_lookup["report.event"]
    assert report_persistor.dropped_readings[(f"{alias}.ta", CHANNEL)] == 0
    assert report_persistor.dropped_readings[(f"{alias}.ta", RENAMED)] == 0
