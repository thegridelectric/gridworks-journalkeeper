"""The house operating status projection: one current status row per house.

Hermetic tests cover the derivation from the old scada code's layout and
snapshot, and the persistence-info contracts (live only). The integration
tests (ephemeral TimescaleDB) prove the row semantics: a scada's word
upserts on the TerminalAsset GNodeId and an older one is skipped, a
derived row is written for a house with a layout and never over a scada
row, a live snapshot refreshes the derived row, and the rebuild from the
journal ends with the scada row winning.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from gw_data.db.models import GNodeSql, HouseOperatingStatusSql, LayoutSql, MessageSql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk.house_operating_status_persistor import HouseOperatingStatusPersistor
from gjk.house_status_projection import (
    SOURCE_DERIVED,
    SOURCE_SCADA,
    HouseStatusProjection,
    derived_status,
)
from gjk.layouts_projection import LayoutsProjection
from gjk.rebuild_house_status import rebuild
from gjk.sema.codec import SemaCodec
from gjk.sema.enums import (
    GwDispatchRefusalReason,
    GwStandbyPosture,
    GwTopState,
    TaValidationState,
)
from gjk.sema.types import GwHouseOperatingStatus, SnapshotSpaceheat
from gjk.snapshot_spaceheat_persistor import SnapshotSpaceheatPersistor

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_012 = ROOT / "src/gjk/sema/definitions/types/layout.lite/012.yaml"
# Oak's real emission from the 2026-10-20 18:31 beta window (jm/spruce-unlimbo
# scada), with the time field as the word spells it after the rename.
SAMPLE_STATUS = (
    ROOT
    / "tests/data/sample_messages/ops473/oak-gw.house.operating.status-000-2026-10-20.json"
)

BEECH_SCADA = "hw1.isone.me.versant.keene.beech.scada"
BEECH_TA = "hw1.isone.me.versant.keene.beech.ta"
BEECH_TA_ID = uuid.UUID("7e152072-c91b-49d2-9ebd-f4fe1b684d06")
LOGGER = logging.getLogger("test_house_status_projection")
CODEC = SemaCodec()
T = 1_790_000_000_000  # a real epoch base; the formats refuse small numbers


def layout_012(created_ms: int, system_mode: str = "Heating") -> dict:
    d = json.loads(yaml.safe_load(EXAMPLE_012.read_text())["examples"][0])
    d["FromGNodeAlias"] = BEECH_SCADA
    d["MessageCreatedMs"] = created_ms
    d["MessageId"] = str(uuid.uuid4())
    d["SystemMode"] = system_mode
    return d


def snapshot(
    time_ms: int, top_state: str = "Auto", auto_state: str = "LocalControl"
) -> dict:
    return {
        "FromGNodeAlias": BEECH_SCADA,
        "FromGNodeInstanceId": str(uuid.uuid4()),
        "SnapshotTimeUnixMs": time_ms,
        "LatestReadingList": [],
        "LatestStateList": [
            {
                "MachineHandle": "s",
                "StateEnum": "top.state",
                "State": top_state,
                "UnixMs": time_ms,
            },
            {
                "MachineHandle": "s.auto",
                "StateEnum": "gw1.main.auto.state",
                "State": auto_state,
                "UnixMs": time_ms,
            },
        ],
        "TypeName": "snapshot.spaceheat",
        "Version": "003",
    }


def status_word(created_ms: int) -> dict:
    d = json.loads(SAMPLE_STATUS.read_text())
    d["ScadaAlias"] = BEECH_SCADA
    d["CreatedMs"] = created_ms
    return d


def decode(d: dict):
    return CODEC.from_dict(d, auto_upgrade=False)


# --- hermetic: the derivation ---------------------------------------------


def test_derived_heating_house_in_auto_accepts_dispatch():
    s = derived_status(decode(layout_012(T + 1_000)), decode(snapshot(T + 2_000)))
    assert isinstance(s, GwHouseOperatingStatus)
    assert s.scada_alias == BEECH_SCADA
    assert s.standby is False
    assert s.standby_posture == GwStandbyPosture.NoHeatingOrCooling
    assert s.accepts_dispatch is True
    assert s.dispatch_refusal_reason is None
    assert s.top_state == GwTopState.Auto
    assert s.ltn_dispatching is False
    assert s.scada_blind is False
    assert s.validation_state == TaValidationState.UnValidated
    assert s.created_ms == T + 2_000  # the newer of the two sources


def test_derived_standby_refuses_as_operator_hold():
    s = derived_status(
        decode(layout_012(T + 1_000, "Standby")), decode(snapshot(T + 500))
    )
    assert s.standby is True
    assert s.accepts_dispatch is False
    assert s.dispatch_refusal_reason == GwDispatchRefusalReason.OperatorHold
    assert s.created_ms == T + 1_000


def test_derived_monitor_only_posture_and_hold():
    s = derived_status(decode(layout_012(T + 1_000, "MonitorOnly")), None)
    assert s.standby is False
    assert s.standby_posture == GwStandbyPosture.MonitorOnly
    assert s.dispatch_refusal_reason == GwDispatchRefusalReason.OperatorHold


def test_derived_admin_refuses_in_admin():
    s = derived_status(
        decode(layout_012(T + 1_000)), decode(snapshot(T + 2_000, top_state="Admin"))
    )
    assert s.top_state == GwTopState.Admin
    assert s.dispatch_refusal_reason == GwDispatchRefusalReason.InAdmin


def test_derived_ltn_dispatching_from_main_auto_state():
    s = derived_status(
        decode(layout_012(T + 1_000)),
        decode(snapshot(T + 2_000, auto_state="LeafTransactiveNode")),
    )
    assert s.ltn_dispatching is True


def test_derived_without_snapshot_assumes_auto():
    s = derived_status(decode(layout_012(T + 1_000)), None)
    assert s.top_state == GwTopState.Auto
    assert s.created_ms == T + 1_000


# --- hermetic: persistence infos ------------------------------------------


def test_status_word_persistence_info_is_live_only_and_at_created_ms():
    projection = HouseStatusProjection(LOGGER)
    info = HouseOperatingStatusPersistor(LOGGER, projection).persist_v000(
        BEECH_SCADA, datetime.now(UTC), decode(status_word(1_700_000_000_000))
    )
    assert info.created_at == datetime.fromtimestamp(1_700_000_000, UTC)
    assert info.additional_db_operations is None
    assert info.live_only_db_operations is not None


def test_snapshot_persistence_info_keeps_its_time_and_id():
    projection = HouseStatusProjection(LOGGER)
    snap = decode(snapshot(1_700_000_000_000))
    assert isinstance(snap, SnapshotSpaceheat)
    info = SnapshotSpaceheatPersistor(LOGGER, projection).persist_v003(
        BEECH_SCADA, datetime.now(UTC), snap
    )
    assert info.created_at == datetime.fromtimestamp(1_700_000_000, UTC)
    assert info.live_only_db_operations is not None
    assert info.additional_db_operations is None


# --- integration ------------------------------------------------------------


@pytest.fixture
def session_factory(timescale_db_url: str):
    eng = create_engine(timescale_db_url)
    factory = sessionmaker(bind=eng)
    with factory.begin() as db:
        db.query(HouseOperatingStatusSql).delete()
        db.query(LayoutSql).delete()
        db.query(MessageSql).filter(
            MessageSql.message_type_name.in_([
                "snapshot.spaceheat",
                "gw.house.operating.status",
            ])
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


def add_message(db, d: dict, type_name: str, time_ms: int) -> MessageSql:
    msg = MessageSql(
        id=uuid.uuid4(),
        timestamp=datetime.fromtimestamp(time_ms / 1000, UTC),
        created_at=datetime.fromtimestamp(time_ms / 1000, UTC),
        persisted_at=datetime.now(UTC),
        from_alias=BEECH_SCADA,
        message_type_name=type_name,
        payload=d,
    )
    db.add(msg)
    db.flush()
    return msg


def row(db) -> HouseOperatingStatusSql | None:
    return db.get(HouseOperatingStatusSql, BEECH_TA_ID)


@pytest.mark.integration
def test_scada_word_upserts_and_older_is_skipped(session_factory):
    projection = HouseStatusProjection(LOGGER)
    with session_factory.begin() as db:
        projection.project_reported(
            db, BEECH_SCADA, decode(status_word(T + 2_000)), str(uuid.uuid4())
        )
        projection.project_reported(
            db, BEECH_SCADA, decode(status_word(T + 1_000)), str(uuid.uuid4())
        )
        r = row(db)
        assert r is not None and r.source == SOURCE_SCADA
        assert r.payload["CreatedMs"] == T + 2_000
        assert r.terminal_asset_alias == BEECH_TA


@pytest.mark.integration
def test_derived_row_from_layout_and_snapshot_never_over_scada(session_factory):
    projection = HouseStatusProjection(LOGGER)
    with session_factory.begin() as db:
        assert projection.derive(db, BEECH_TA) is False  # no layout yet
        LayoutsProjection(LOGGER).project(
            db, BEECH_SCADA, decode(layout_012(T + 1_000, "Standby"))
        )
        add_message(
            db, snapshot(T + 2_000, top_state="Admin"), "snapshot.spaceheat", T + 2_000
        )
        assert projection.derive(db, BEECH_TA) is True
        r = row(db)
        assert r is not None and r.source == SOURCE_DERIVED and r.message_id is None
        assert r.payload["Standby"] is True and r.payload["TopState"] == "Admin"
        assert r.payload["CreatedMs"] == T + 2_000

        projection.project_reported(
            db, BEECH_SCADA, decode(status_word(T + 500)), str(uuid.uuid4())
        )
        assert (
            row(db).source == SOURCE_SCADA
        )  # a scada word replaces a derived row at any time
        assert projection.derive(db, BEECH_TA) is False
        assert row(db).source == SOURCE_SCADA


@pytest.mark.integration
def test_rebuild_derives_then_reports(session_factory):
    projection = HouseStatusProjection(LOGGER)
    with session_factory.begin() as db:
        LayoutsProjection(LOGGER).project(
            db, BEECH_SCADA, decode(layout_012(T + 1_000))
        )
        add_message(db, snapshot(T + 1_500), "snapshot.spaceheat", T + 1_500)
        assert rebuild(db, projection) == (1, 0)
        assert row(db).source == SOURCE_DERIVED
        add_message(db, status_word(T + 3_000), "gw.house.operating.status", T + 3_000)
        assert rebuild(db, projection) == (1, 1)
        r = row(db)
        assert r.source == SOURCE_SCADA and r.payload["CreatedMs"] == T + 3_000
