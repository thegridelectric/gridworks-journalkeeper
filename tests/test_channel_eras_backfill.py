"""Back-filling old layouts and reports into a DB that already holds the
current era, against real TimescaleDB, with real beech wire samples.

beech `buffer-depth1` was a `WaterTempCTimes1000` data channel through 2025
and is a `FahrenheitX100` derived channel from 2026. Loading the 2025 layout
after the 2026 one must leave the live channel active, record the old
definition as a retired era row, and route each era's readings to the row
with its unit. Before the time-aware sync the 2025 layout deactivated the
live channel; before the era lookup the 2025 readings landed on the °F row.
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
LAYOUT_2026 = "beech-layout.lite-011-2026-07-25.json"
LAYOUT_2025 = "beech-layout.lite-004-2025-10-15.json"
REPORT_2024 = "beech-report.event-000-2024-10-28.json"
REPORT_2025 = "beech-report.event-002-2025-10-13.json"
REPORT_2026 = "beech-report.event-002-2026-07-25.json"

pytestmark = pytest.mark.integration


def _load(name: str, alias: str, shift_ms: int = 0) -> dict:
    """Read a sample, re-homing it from beech to `alias` (message id included,
    so the messages row is unique per test) and optionally shifting its
    creation time."""
    text = (SAMPLES / name).read_text().replace(BEECH, alias)
    payload = json.loads(text)
    seed = f"{alias}|{payload['MessageId']}"
    new_id = str(uuid.UUID(int=random.Random(seed).getrandbits(128), version=4))
    payload["MessageId"] = new_id
    if "Report" in payload and "Id" in payload["Report"]:
        payload["Report"]["Id"] = new_id
    if shift_ms:
        if "TimeCreatedMs" in payload:
            payload["TimeCreatedMs"] += shift_ms
            payload["Report"]["MessageCreatedMs"] += shift_ms
        else:
            payload["MessageCreatedMs"] += shift_ms
    return payload


def _created_ms(payload: dict) -> int:
    return payload.get("MessageCreatedMs") or payload["TimeCreatedMs"]


def _persist(persistor, codec, payload: dict, alias: str):
    obj = codec.from_dict(payload, auto_upgrade=False)
    persistor.persist_message(
        f"{alias}.scada",
        datetime.fromtimestamp(_created_ms(payload) / 1000, UTC),
        obj,
    )


def _channel_rows(db: Session, alias: str, name: str) -> list[ReadingChannelSql]:
    return (
        db
        .query(ReadingChannelSql)
        .filter(
            ReadingChannelSql.terminal_asset_alias == f"{alias}.ta",
            ReadingChannelSql.name == name,
        )
        .all()
    )


def _readings(db: Session, channel_id: uuid.UUID) -> list[ReadingSql]:
    return db.query(ReadingSql).filter(ReadingSql.channel_id == channel_id).all()


@pytest.fixture
def persistor(timescale_db_url):
    from gjk.config import Settings
    from gjk.sema import SemaCodec
    from gjk.sema_message_persistor import SemaMessagePersistor

    settings = Settings(
        db_url=SecretStr(timescale_db_url),
        service_alias="d1.journal",
    )
    return SemaMessagePersistor(settings, SemaCodec(), logging.getLogger("test"))


@pytest.fixture
def db(timescale_db_url):
    engine = create_engine(timescale_db_url)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_old_layout_after_new_keeps_live_channels_and_adds_era_row(persistor, db):
    alias = f"{BEECH}.eras1"
    codec = persistor.codec
    layout_2026 = _load(LAYOUT_2026, alias)
    layout_2025 = _load(LAYOUT_2025, alias)

    _persist(persistor, codec, layout_2026, alias)
    active_before = {
        c.name: c.id
        for c in db
        .query(ReadingChannelSql)
        .filter(
            ReadingChannelSql.terminal_asset_alias == f"{alias}.ta",
            ReadingChannelSql.deactivated_date.is_(None),
        )
        .all()
    }
    [derived] = _channel_rows(db, alias, "buffer-depth1")
    assert derived.unit == "FahrenheitX100"

    _persist(persistor, codec, layout_2025, alias)
    db.expire_all()

    active_after = {
        c.name: c.id
        for c in db
        .query(ReadingChannelSql)
        .filter(
            ReadingChannelSql.terminal_asset_alias == f"{alias}.ta",
            ReadingChannelSql.deactivated_date.is_(None),
        )
        .all()
    }
    # The active set is exactly what the 2026 layout made it; 2025-only
    # channels became era rows, not live ones.
    assert active_before == active_after
    old_only = (
        db
        .query(ReadingChannelSql)
        .filter(
            ReadingChannelSql.terminal_asset_alias == f"{alias}.ta",
            ReadingChannelSql.deactivated_date.isnot(None),
        )
        .count()
    )
    assert old_only > 1

    rows = {
        (r.unit, r.deactivated_date) for r in _channel_rows(db, alias, "buffer-depth1")
    }
    boundary = datetime.fromtimestamp(_created_ms(layout_2026) / 1000, UTC)
    assert rows == {("FahrenheitX100", None), ("WaterTempCTimes1000", boundary)}
    assert (
        persistor.custom_persistor_lookup["layout.lite"].skipped_mismatches[
            (f"{alias}.ta", "buffer-depth1")
        ]
        == 1
    )

    # Re-running the old layout is a no-op.
    _persist(persistor, codec, layout_2025, alias)
    db.expire_all()
    assert len(_channel_rows(db, alias, "buffer-depth1")) == 2


def test_readings_route_to_the_era_with_their_unit(persistor, db):
    alias = f"{BEECH}.eras2"
    codec = persistor.codec
    _persist(persistor, codec, _load(LAYOUT_2026, alias), alias)
    _persist(persistor, codec, _load(LAYOUT_2025, alias), alias)
    _persist(persistor, codec, _load(REPORT_2024, alias), alias)
    _persist(persistor, codec, _load(REPORT_2025, alias), alias)
    # The 2026 sample report precedes the 2026 layout by 45 minutes on the
    # same day; a report a day later sits squarely in the derived era.
    _persist(persistor, codec, _load(REPORT_2026, alias, shift_ms=86_400_000), alias)
    db.expire_all()

    by_unit = {r.unit: r for r in _channel_rows(db, alias, "buffer-depth1")}
    celsius = sorted(
        _readings(db, by_unit["WaterTempCTimes1000"].id), key=lambda r: r.timestamp
    )
    fahrenheit = _readings(db, by_unit["FahrenheitX100"].id)

    # Oct 2024 (before any layout existed) and Oct 2025 both sit in the
    # WaterTempCTimes1000 era; Jul 2026 in the FahrenheitX100 era.
    assert {r.timestamp.year for r in celsius} == {2024, 2025}
    assert celsius[0].value == 68830
    assert any(r.value == 23120 for r in celsius)
    assert {r.timestamp.year for r in fahrenheit} == {2026}
    assert any(r.value == 5921 for r in fahrenheit)
    report_persistor = persistor.custom_persistor_lookup["report.event"]
    assert report_persistor.dropped_readings[(f"{alias}.ta", "buffer-depth1")] == 0


def test_forward_order_still_deactivates_on_definition_change(persistor, db):
    """The live path: a newer layout with a changed definition retires the
    old row at its own time — the same era shape the back-fill produces."""
    alias = f"{BEECH}.eras3"
    codec = persistor.codec
    layout_2025 = _load(LAYOUT_2025, alias)
    layout_2026 = _load(LAYOUT_2026, alias)
    _persist(persistor, codec, layout_2025, alias)
    _persist(persistor, codec, layout_2026, alias)
    db.expire_all()

    rows = {
        (r.unit, r.deactivated_date) for r in _channel_rows(db, alias, "buffer-depth1")
    }
    boundary = datetime.fromtimestamp(_created_ms(layout_2026) / 1000, UTC)
    assert rows == {("FahrenheitX100", None), ("WaterTempCTimes1000", boundary)}
