"""The report persistor checks every resolved row against the layout in
force: the row's `channel_id` is the Id the layout declares for the name.
A drifted row is tallied on every report, back-filled or live, and a live
report journals one Warning glitch per (asset, channel, declared Id, row
Id) per UTC day under the journalkeeper's own alias.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from gw_data.db.models import MessageSql, ReadingChannelSql
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from gjk.report_event_persistor import GLITCH_NODE, MismatchKey
from tests.test_channel_identity_toggle import (
    BEECH,
    CHANNEL,
    HOUR_MS,
    LAYOUT,
    REPORT,
    _created_ms,
    _load,
)

SERVICE_ALIAS = "d1.journal"

pytestmark = pytest.mark.integration


@pytest.fixture
def persistor(timescale_db_url):
    from gjk.config import Settings
    from gjk.sema import SemaCodec
    from gjk.sema_message_persistor import SemaMessagePersistor

    settings = Settings(db_url=SecretStr(timescale_db_url), service_alias=SERVICE_ALIAS)
    return SemaMessagePersistor(settings, SemaCodec(), logging.getLogger("test"))


@pytest.fixture
def db(timescale_db_url):
    engine = create_engine(timescale_db_url)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _persist(persistor, payload: dict, alias: str, *, live: bool):
    obj = persistor.codec.from_dict(payload, auto_upgrade=False)
    persistor.persist_message(
        f"{alias}.scada",
        datetime.fromtimestamp(_created_ms(payload) / 1000, UTC),
        obj,
        live=live,
    )


def _noon_shift_ms(payload: dict) -> int:
    """The shift that puts the sample at 12:00 UTC of its own day, so hours
    added to it stay on one UTC day and a day later is one day later."""
    created = datetime.fromtimestamp(_created_ms(payload) / 1000, UTC)
    noon = created.replace(hour=12, minute=0, second=0, microsecond=0)
    return int((noon - created).total_seconds() * 1000)


def test_drifted_channel_id_is_tallied_and_glitched_once_a_day(persistor, db):
    alias = f"{BEECH}.idcheck1"
    base = _noon_shift_ms(_load(LAYOUT, alias, 0))
    layout = _load(LAYOUT, alias, base)
    [channel] = [c for c in layout["DataChannels"] if c["Name"] == CHANNEL]
    declared_id = uuid.UUID(channel["Id"])
    _persist(persistor, layout, alias, live=True)

    row = (
        db
        .query(ReadingChannelSql)
        .filter(
            ReadingChannelSql.terminal_asset_alias == f"{alias}.ta",
            ReadingChannelSql.name == CHANNEL,
        )
        .one()
    )
    assert row.channel_id == declared_id
    drifted = uuid.uuid4()
    row.channel_id = drifted
    db.commit()

    def report(hours: int) -> dict:
        return _load(REPORT, alias, base + hours * HOUR_MS)

    def n_readings(payload: dict) -> int:
        [readings] = [
            c
            for c in payload["Report"]["ChannelReadingList"]
            if c["ChannelName"] == CHANNEL
        ]
        return len(readings["ValueList"])

    def glitches() -> list[MessageSql]:
        db.expire_all()
        rows = (
            db
            .query(MessageSql)
            .filter(
                MessageSql.from_alias == SERVICE_ALIAS,
                MessageSql.message_type_name == "glitch",
            )
            .order_by(MessageSql.timestamp)
            .all()
        )
        return [m for m in rows if alias in m.payload["Summary"]]

    report_persistor = persistor.custom_persistor_lookup["report.event"]
    key = MismatchKey(f"{alias}.ta", CHANNEL, declared_id, drifted)
    first = report(1)
    n = n_readings(first)

    # a back-filled report tallies and journals nothing
    _persist(persistor, first, alias, live=False)
    assert report_persistor.channel_id_mismatches[key] == n
    assert glitches() == []

    # the first live report of the day journals one glitch with the count
    _persist(persistor, report(2), alias, live=True)
    assert report_persistor.channel_id_mismatches[key] == 2 * n
    [glitch] = glitches()
    assert glitch.payload["Type"] == "Warning"
    assert glitch.payload["Node"] == GLITCH_NODE
    assert glitch.payload["FromGNodeAlias"] == SERVICE_ALIAS
    assert str(declared_id) in glitch.payload["Details"]
    assert str(drifted) in glitch.payload["Details"]
    assert f"{2 * n} readings" in glitch.payload["Details"]
    assert glitch.timestamp == datetime.fromtimestamp(
        _created_ms(report(2)) / 1000, UTC
    )

    # a second live report the same day tallies and journals no second glitch
    _persist(persistor, report(3), alias, live=True)
    assert report_persistor.channel_id_mismatches[key] == 3 * n
    assert len(glitches()) == 1

    # the next day's first live report journals the second
    next_day = report(26)
    assert (
        datetime.fromtimestamp(_created_ms(next_day) / 1000, UTC).date()
        == (glitch.timestamp + timedelta(days=1)).date()
    )
    _persist(persistor, next_day, alias, live=True)
    assert len(glitches()) == 2

    # a row that agrees with the layout tallies nothing
    row.channel_id = declared_id
    db.commit()
    _persist(persistor, report(27), alias, live=True)
    assert report_persistor.channel_id_mismatches[key] == 4 * n
    assert len(glitches()) == 2
