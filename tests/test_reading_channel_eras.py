"""Hermetic tests for the era lookup and the persistor load tallies. No DB."""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

from gw_data.db.models import ReadingChannelSql

from gjk.reading_channel_eras import channel_ids_at
from gjk.report_event_persistor import ReportEventPersistor
from gjk.s3_message_importer import RunSummary, S3MessageInfo
from gjk.sema import SemaCodec

SAMPLES = Path(__file__).parent / "data" / "sample_messages" / "ops498"


def _row(name, deactivated=None):
    return ReadingChannelSql(
        id=uuid.uuid4(),
        name=name,
        terminal_asset_alias="x.ta",
        display_name=name,
        unit="u",
        unit_type="t",
        channel_type="c",
        deactivated_date=deactivated,
    )


def _t(y, m, d):
    return datetime(y, m, d, tzinfo=UTC)


def test_channel_ids_at_picks_era_containing_time():
    era1 = _row("a", deactivated=_t(2025, 3, 1))
    era2 = _row("a", deactivated=_t(2026, 1, 9))
    active = _row("a")
    only_active = _row("b")
    rows = [active, era2, era1, only_active]

    assert channel_ids_at(rows, _t(2024, 10, 13))["a"] == era1.id
    assert channel_ids_at(rows, _t(2025, 10, 13))["a"] == era2.id
    assert channel_ids_at(rows, _t(2026, 7, 25))["a"] == active.id
    assert channel_ids_at(rows, _t(2024, 10, 13))["b"] == only_active.id


def test_channel_ids_at_ignores_names_with_only_past_eras():
    rows = [_row("gone", deactivated=_t(2025, 1, 1))]
    assert channel_ids_at(rows, _t(2025, 6, 1)) == {}


def test_report_persistor_tallies_dropped_readings_when_no_channels():
    persistor = ReportEventPersistor(logging.getLogger("test"))
    report = SemaCodec().from_dict(
        json.loads((SAMPLES / "beech-report.event-002-2025-10-13.json").read_text()),
        auto_upgrade=False,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    persistor.persist_readings(db, "hw1.isone.me.versant.keene.beech.scada", report)

    dropped = persistor.dropped_readings
    ta = "hw1.isone.me.versant.keene.beech.ta"
    assert dropped[(ta, "buffer-depth1")] == len(
        next(
            c.value_list
            for c in report.report.channel_reading_list
            if c.channel_name == "buffer-depth1"
        )
    )
    assert sum(dropped.values()) >= sum(
        len(c.value_list) for c in report.report.channel_reading_list
    )
    db.execute.assert_not_called()


def test_run_summary_counts_per_day_and_serializes():
    summary = RunSummary()
    info = S3MessageInfo(
        "hw1__1/eventstore/20251013/hw1.isone.me.versant.keene.beech.scada-report.event-1760313900080-1.2.3.4.json"
    )
    summary.count(info, "report.event", "002", "ok")
    summary.count(info, "report.event", "002", "ok")
    summary.count(info, "layout.lite", "004", "degraded")
    summary.messages_processed = 3
    summary.dropped_readings[("x.ta", "ch")] = 5

    out = summary.to_jsonable()
    assert summary.versions[("report.event", "002")].ok == 2
    assert {
        "day": "2025-10-13",
        "from_alias": "hw1.isone.me.versant.keene.beech.scada",
        "type_name": "report.event",
        "version": "002",
        "outcome": "ok",
        "count": 2,
    } in out["daily"]
    assert out["dropped_readings"] == [
        {"terminal_asset_alias": "x.ta", "channel": "ch", "count": 5}
    ]
    json.dumps(out)
