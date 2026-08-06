"""g.node.forest fan-out: registry projection into gw_data.

Hermetic tests cover the persistence-info contract and registration; the
integration test (ephemeral TimescaleDB) proves the projection semantics —
upsert on immutable ids, replay idempotency, alias update on reparent,
missing-endpoint edge skip, and (from, to) pair supersede.
"""

import logging
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from gw_data.db.models import ConnectivityEdgeSql, GNodeSql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk.g_node_forest_persistor import GNodeForestPersistor
from gjk.message_persistence_info import default_message_id
from gjk.sema.enums import BaseGNodeClass, GNodeStatus
from gjk.sema.types import ConnectivityEdgeGt, GNodeForest, GNodeGt

FROM_ALIAS = "hw1.gnr"
PERSISTED_MS = 1785000000000

ID_A = "11111111-1111-4111-8111-111111111111"
ID_B = "22222222-2222-4222-8222-222222222222"
ID_X = "33333333-3333-4333-8333-333333333333"  # never projected
EDGE_1 = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
EDGE_2 = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
POINT_P = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"  # opaque registry id, stored verbatim


def _t(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def _node(g_node_id: str, alias: str, position_point_id: str | None = None) -> GNodeGt:
    if position_point_id is None:
        return GNodeGt(
            g_node_id=g_node_id,
            alias=alias,
            base_class=BaseGNodeClass.Logical,
            g_node_class="Logical",
            status=GNodeStatus.Active,
        )
    return GNodeGt(
        g_node_id=g_node_id,
        alias=alias,
        base_class=BaseGNodeClass.LeafTransactiveNode,
        g_node_class="LeafTransactiveNode",
        status=GNodeStatus.Active,
        position_point_id=position_point_id,
    )


def _edge(edge_id: str, from_id: str, to_id: str) -> ConnectivityEdgeGt:
    return ConnectivityEdgeGt(
        id=edge_id,
        from_g_node_id=from_id,
        to_g_node_id=to_id,
        status=GNodeStatus.Active,
    )


SEND_TIME_MS = 1785971400000


def _forest(
    nodes: list[GNodeGt],
    edges: list[ConnectivityEdgeGt],
    send_time_ms: int = SEND_TIME_MS,
) -> GNodeForest:
    return GNodeForest(
        roots=["d1.iso"], nodes=nodes, edges=edges, send_time_ms=send_time_ms
    )


def test_forest_persistor_id_is_deterministic_uuid5():
    p = GNodeForestPersistor(
        logging.getLogger("test_forest_persistor"), registry_alias=FROM_ALIAS
    )
    forest = MagicMock()
    t = _t(PERSISTED_MS)

    id1 = p.persist_v000(FROM_ALIAS, t, forest).id
    id2 = p.persist_v000(FROM_ALIAS, t, forest).id

    assert id1 == id2
    assert id1 == default_message_id(FROM_ALIAS, "g.node.forest", t)
    assert p.persist_v000(FROM_ALIAS, _t(PERSISTED_MS + 1000), forest).id != id1


def test_forest_v001_send_time_becomes_created_at():
    """SendTimeMs (the registry's clock at forest assembly) is the message's
    created_at; absent on a v001 without it, and on all v000."""
    p = GNodeForestPersistor(
        logging.getLogger("test_forest_persistor"), registry_alias=FROM_ALIAS
    )
    t = _t(PERSISTED_MS)

    with_time = MagicMock(send_time_ms=PERSISTED_MS - 5000)
    info = p.persist_v001(FROM_ALIAS, t, with_time)
    assert info.created_at == _t(PERSISTED_MS - 5000)
    assert info.id == default_message_id(FROM_ALIAS, "g.node.forest", t)

    without_time = MagicMock(send_time_ms=None)
    assert p.persist_v001(FROM_ALIAS, t, without_time).created_at is None
    assert p.persist_v000(FROM_ALIAS, t, MagicMock()).created_at is None


def test_forest_from_non_registry_witnessed_not_projected():
    """Only the universe's registry may shape the projection: any other
    from_alias gets its raw message persisted (the id still derives) but
    no fan-out."""
    p = GNodeForestPersistor(
        logging.getLogger("test_forest_persistor"), registry_alias="hw1.gnr"
    )
    t = _t(PERSISTED_MS)

    rogue = p.persist_v001("hw1.isone.rogue", t, MagicMock(send_time_ms=None))
    assert rogue.additional_db_operations is None
    assert rogue.id == default_message_id("hw1.isone.rogue", "g.node.forest", t)

    legit = p.persist_v001("hw1.gnr", t, MagicMock(send_time_ms=None))
    assert legit.additional_db_operations is not None
    assert (
        p.persist_v000("hw1.isone.rogue", t, MagicMock()).additional_db_operations
        is None
    )


def test_forest_persistor_registered_not_basic():
    from gjk.sema_message_persistor import SemaMessagePersistor

    assert "g.node.forest" not in SemaMessagePersistor.BASIC_MSG_TYPES
    # registration is via custom_persistor_lookup (instance-level); the class
    # wiring is proven by the persistor's target_message_type
    p = GNodeForestPersistor(
        logging.getLogger("test_forest_persistor"), registry_alias=FROM_ALIAS
    )
    assert p.target_message_type == "g.node.forest"
    assert p.fanout_on_import is False  # current-state projection; live only


def _dispatch_persistor_with(forest_persistor):
    """A SemaMessagePersistor shell wired to the forest persistor, no DB."""
    from contextlib import contextmanager

    from gjk.sema_message_persistor import SemaMessagePersistor

    p = SemaMessagePersistor.__new__(SemaMessagePersistor)
    p.logger = logging.getLogger("test_forest_persistor")
    p.custom_persistor_lookup = {"g.node.forest": forest_persistor}

    @contextmanager
    def _fake_db():
        yield MagicMock()

    p.get_db = _fake_db
    return p


@pytest.mark.parametrize(("live", "fanout_runs"), [(True, True), (False, False)])
def test_forest_fanout_runs_only_live(live: bool, fanout_runs: bool):
    """A persistent-store replay must not touch the current-state projection:
    the dispatch seam drops the forest persistor's additional_db_operations
    when live=False (raw message still persisted either way)."""
    forest_persistor = GNodeForestPersistor(
        logging.getLogger("test"), registry_alias=FROM_ALIAS
    )
    p = _dispatch_persistor_with(forest_persistor)
    upserts: list[object] = []
    forest_persistor.project_forest = lambda db, forest: upserts.append(forest)

    payload = MagicMock(version="000")
    payload.type_name = "g.node.forest"
    payload.to_dict.return_value = {}

    p.persist_message(FROM_ALIAS, _t(PERSISTED_MS), payload, live=live)

    assert bool(upserts) is fanout_runs


@pytest.mark.integration
def test_forest_projection_converges(timescale_db_url: str):
    p = GNodeForestPersistor(
        logging.getLogger("test_forest_persistor"), registry_alias=FROM_ALIAS
    )
    eng = create_engine(timescale_db_url)
    Session = sessionmaker(bind=eng)

    node_a = _node(ID_A, "d1.iso")
    node_b = _node(ID_B, "d1.iso.keene", position_point_id=POINT_P)

    # 1. First projection: two nodes + the edge wiring them. B's opaque
    #    position id stores verbatim — gw_data holds no position content
    #    to resolve against.
    with Session.begin() as db:
        p.project_forest(db, _forest([node_a, node_b], [_edge(EDGE_1, ID_A, ID_B)]))
    with Session() as db:
        assert db.query(GNodeSql).count() == 2
        b = db.get(GNodeSql, ID_B)
        assert b.alias == "d1.iso.keene"
        assert b.position_point_id == uuid.UUID(POINT_P)
        assert db.get(ConnectivityEdgeSql, EDGE_1) is not None

    # 2. Replay of the same forest is a no-op (idempotent).
    with Session.begin() as db:
        p.project_forest(db, _forest([node_a, node_b], [_edge(EDGE_1, ID_A, ID_B)]))
    with Session() as db:
        assert db.query(GNodeSql).count() == 2
        assert db.query(ConnectivityEdgeSql).count() == 1

    # 3. Reparent-style update: same id, new alias + prev_alias -> row updates.
    node_b2 = _node(ID_B, "d1.iso.maine.keene", position_point_id=POINT_P)
    node_b2 = node_b2.model_copy(update={"prev_alias": "d1.iso.keene"})
    with Session.begin() as db:
        p.project_forest(db, _forest([node_b2], []))
    with Session() as db:
        b = db.get(GNodeSql, ID_B)
        assert b.alias == "d1.iso.maine.keene"
        assert b.prev_alias == "d1.iso.keene"
        assert db.query(GNodeSql).count() == 2

    # 3b. Do-not-regress: an OLDER forest re-asserting the pre-reparent alias
    #     is skipped (equal send times pass — that's step 2's idempotency).
    stale = _node(ID_B, "d1.iso.keene", position_point_id=POINT_P)
    with Session.begin() as db:
        p.project_forest(db, _forest([stale], [], send_time_ms=SEND_TIME_MS - 60_000))
    with Session() as db:
        b = db.get(GNodeSql, ID_B)
        assert b.alias == "d1.iso.maine.keene"
        assert b.sent_at == _t(SEND_TIME_MS)

    # 4. An edge whose endpoint was never projected is skipped, not an error.
    with Session.begin() as db:
        p.project_forest(db, _forest([], [_edge(EDGE_2, ID_X, ID_A)]))
    with Session() as db:
        assert db.query(ConnectivityEdgeSql).count() == 1

    # 5. Edge ids are immutable per (from, to) pair: a new id claiming an
    #    existing pair is an anomaly — skipped with a warning, the standing
    #    row untouched.
    with Session.begin() as db:
        p.project_forest(db, _forest([], [_edge(EDGE_2, ID_A, ID_B)]))
    with Session() as db:
        assert db.get(ConnectivityEdgeSql, EDGE_1) is not None
        assert db.get(ConnectivityEdgeSql, EDGE_2) is None
        assert db.query(ConnectivityEdgeSql).count() == 1

    eng.dispose()
