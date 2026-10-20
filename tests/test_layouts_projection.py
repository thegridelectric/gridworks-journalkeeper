"""The layouts projection: one current layout row per terminal asset,
written from live layout.lite messages only, guarded on the sender's clock.

Hermetic tests cover the persistence-info contract and the live-only seam;
the integration tests (ephemeral TimescaleDB) prove the projection
semantics: upsert on the TerminalAsset GNodeId, an older send time skipped,
a lower word version with a later send time winning, an unregistered
terminal asset skipped, a registry-written row kept, and the rebuild from
journaled messages.
"""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from gw_data.db.models import GNodeSql, LayoutSql, MessageSql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk.layout_lite_persistor import LayoutLitePersistor
from gjk.layouts_projection import LayoutsProjection, terminal_asset_alias
from gjk.rebuild_layouts import rebuild
from gjk.sema.codec import SemaCodec
from gjk.sema_message_persistor import SemaMessagePersistor

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_011 = (
    ROOT / "tests/data/sample_messages/ops498/beech-layout.lite-011-2026-07-25.json"
)
EXAMPLE_012 = ROOT / "src/gjk/sema/definitions/types/layout.lite/012.yaml"

BEECH_SCADA = "hw1.isone.me.versant.keene.beech.scada"
BEECH_TA = "hw1.isone.me.versant.keene.beech.ta"
OAK_SCADA = "hw1.isone.me.versant.keene.oak.scada"
BEECH_TA_ID = uuid.UUID("7e152072-c91b-49d2-9ebd-f4fe1b684d06")
LOGGER = logging.getLogger("test_layouts_projection")


def decode(codec: SemaCodec, d: dict):
    """As the live path decodes: the word at the version it was sent."""
    return codec.from_dict(d, auto_upgrade=False)


def layout_011(created_ms: int, scada: str = BEECH_SCADA) -> dict:
    d = json.loads(FIXTURE_011.read_text())
    d["FromGNodeAlias"] = scada
    d["MessageCreatedMs"] = created_ms
    d["MessageId"] = str(uuid.uuid4())
    return d


def layout_012(created_ms: int, scada: str = BEECH_SCADA) -> dict:
    d = json.loads(yaml.safe_load(EXAMPLE_012.read_text())["examples"][0])
    d["FromGNodeAlias"] = scada
    d["MessageCreatedMs"] = created_ms
    d["MessageId"] = str(uuid.uuid4())
    return d


def test_terminal_asset_alias_from_scada_alias():
    assert terminal_asset_alias(BEECH_SCADA) == BEECH_TA


def test_layout_lite_persistence_info_projects_live_only():
    p = LayoutLitePersistor(LOGGER)
    info = p.persist_v011(
        BEECH_SCADA, datetime.now(UTC), decode(SemaCodec(), layout_011(1784940626155))
    )
    assert (
        info.additional_db_operations is not None
    )  # the channel sync, replays welcome
    assert info.live_only_db_operations is not None  # the projection, live only


@pytest.mark.parametrize(("live", "projected"), [(True, True), (False, False)])
def test_projection_runs_only_live(live: bool, projected: bool):
    """A persistent-store replay syncs channels as before and leaves the
    layouts projection alone."""
    persistor = LayoutLitePersistor(LOGGER)
    projected_layouts: list[object] = []
    synced: list[object] = []
    persistor.layouts.project = lambda db, from_alias, layout: projected_layouts.append(
        layout
    )
    persistor.sync_reading_channels = lambda db, from_alias, layout: synced.append(
        layout
    )

    shell = SemaMessagePersistor.__new__(SemaMessagePersistor)
    shell.logger = LOGGER
    shell.custom_persistor_lookup = {"layout.lite": persistor}

    @contextmanager
    def fake_db():
        yield MagicMock()

    shell.get_db = fake_db
    payload = decode(SemaCodec(), layout_011(1784940626155))
    shell.persist_message(BEECH_SCADA, datetime.now(UTC), payload, live=live)

    assert len(synced) == 1
    assert bool(projected_layouts) is projected


@pytest.fixture
def session_factory(timescale_db_url: str):
    eng = create_engine(timescale_db_url)
    factory = sessionmaker(bind=eng)
    with factory.begin() as db:
        db.query(LayoutSql).delete()
        db.query(MessageSql).filter(
            MessageSql.message_type_name == "layout.lite"
        ).delete()
        if db.get(GNodeSql, BEECH_TA_ID) is None:
            db.add(
                GNodeSql(
                    id=BEECH_TA_ID,
                    alias=BEECH_TA,
                    base_class="TerminalAsset",
                    g_node_class="TerminalAsset",
                    status="Active",
                )
            )
    yield factory
    eng.dispose()


def current_row(factory) -> LayoutSql | None:
    with factory() as db:
        row = db.get(LayoutSql, BEECH_TA_ID)
        if row is not None:
            db.expunge(row)
        return row


@pytest.mark.integration
def test_projection_follows_the_sender_clock(session_factory):
    codec = SemaCodec()
    projection = LayoutsProjection(LOGGER)
    t0 = 1784940626155

    with session_factory.begin() as db:
        projection.project(db, BEECH_SCADA, decode(codec, layout_011(t0)))
    row = current_row(session_factory)
    assert (row.terminal_asset_alias, row.from_alias, row.type_name, row.version) == (
        BEECH_TA,
        BEECH_SCADA,
        "layout.lite",
        "011",
    )
    assert row.sent_at == datetime.fromtimestamp(t0 / 1000, UTC)
    assert row.payload["MessageCreatedMs"] == t0

    # An older assertion, even of a newer word version, is skipped.
    with session_factory.begin() as db:
        projection.project(db, BEECH_SCADA, decode(codec, layout_012(t0 - 1000)))
    assert current_row(session_factory).version == "011"

    # A later assertion wins.
    with session_factory.begin() as db:
        projection.project(db, BEECH_SCADA, decode(codec, layout_012(t0 + 1000)))
    assert current_row(session_factory).version == "012"

    # A lower word version with a later send time wins: the row follows
    # the house back from the newer branch.
    with session_factory.begin() as db:
        projection.project(db, BEECH_SCADA, decode(codec, layout_011(t0 + 2000)))
    row = current_row(session_factory)
    assert row.version == "011"
    assert row.payload["MessageCreatedMs"] == t0 + 2000

    with session_factory() as db:
        assert db.query(LayoutSql).count() == 1


@pytest.mark.integration
def test_unregistered_terminal_asset_is_not_projected(session_factory):
    projection = LayoutsProjection(LOGGER)
    with session_factory.begin() as db:
        projection.project(
            db, OAK_SCADA, decode(SemaCodec(), layout_011(1784940626155, OAK_SCADA))
        )
    with session_factory() as db:
        assert db.query(LayoutSql).count() == 0


@pytest.mark.integration
def test_registry_written_row_is_kept(session_factory):
    codec = SemaCodec()
    projection = LayoutsProjection(LOGGER, registry_alias="hw1.tar")
    t0 = 1784940626155
    with session_factory.begin() as db:
        projection.project(db, BEECH_SCADA, decode(codec, layout_011(t0)))
        db.get(LayoutSql, BEECH_TA_ID).from_alias = "hw1.tar"

    with session_factory.begin() as db:
        projection.project(db, BEECH_SCADA, decode(codec, layout_012(t0 + 1000)))
    row = current_row(session_factory)
    assert (row.from_alias, row.version) == ("hw1.tar", "011")


@pytest.mark.integration
def test_rebuild_fills_the_table_from_journaled_messages(session_factory):
    codec = SemaCodec()
    t0 = 1784940626155
    with session_factory.begin() as db:
        for created_ms, payload in (
            (t0 + 5000, layout_012(t0 + 5000)),
            (t0, layout_011(t0)),
        ):
            db.add(
                MessageSql(
                    id=uuid.UUID(payload["MessageId"]),
                    timestamp=datetime.fromtimestamp(created_ms / 1000, UTC),
                    created_at=datetime.fromtimestamp(created_ms / 1000, UTC),
                    persisted_at=datetime.now(UTC),
                    from_alias=BEECH_SCADA,
                    message_type_name="layout.lite",
                    payload=payload,
                )
            )
    with session_factory() as db:
        assert db.query(LayoutSql).count() == 0

    with session_factory.begin() as db:
        assert rebuild(db, codec, LayoutsProjection(LOGGER)) == 1
    row = current_row(session_factory)
    assert row.version == "012"
    assert row.payload["MessageCreatedMs"] == t0 + 5000
