"""Fan out g.node.forest broadcasts into gw_data's registry projection.

The registry (gnr) broadcasts a forest — current GNodes plus the active
non-tree connectivity edges wiring them — after every applied command and
as a periodic snapshot. This persistor upserts that content into
``gridworks.g_nodes`` / ``gridworks.connectivity_edges``, keyed on the
immutable ids, so deltas, snapshots, and replays all converge to the same
rows. The parent-child tree itself is carried by the alias prefix, not by
edge rows, and the registry's alias ledger guarantees an alias is only
ever owned by one GNodeId — so per-row upserts cannot collide.

The projection is CURRENT state, so replayed history must not touch it:
``fanout_on_import = False`` means the dispatch seam runs this fan-out only
for live broker messages, never for persistent-store backfills (the raw
message is stored either way). The periodic snapshot broadcast keeps the
projection converged.
"""

import uuid
from datetime import UTC, datetime

from gw_data.db.models import ConnectivityEdgeSql, GNodeSql
from gw_data.sema.enums import BaseGNodeClass as DbBaseGNodeClass
from gw_data.sema.enums import GNodeStatus as DbGNodeStatus
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.sema.types import ConnectivityEdgeGt, GNodeForest, GNodeGt
from gjk.sema.types.old_versions.g_node_forest_000 import GNodeForest000
from gjk.sema.types.old_versions.g_node_forest_001 import GNodeForest001

type AnyForest = GNodeForest | GNodeForest000 | GNodeForest001


class GNodeForestPersistor:
    def __init__(self, logger, registry_alias: str):
        self.logger = logger
        self.target_message_type = "g.node.forest"
        self.fanout_on_import = False  # current-state projection; live only
        # The one sender whose forests this projection trusts. from_alias
        # is self-asserted in the routing key until the broker enforces
        # publish-time alias pinning; either way, only the universe's
        # registry may shape current state here.
        self.registry_alias = registry_alias

    def _fanout_if_registry(self, from_alias: str, forest: "AnyForest"):
        if from_alias != self.registry_alias:
            self.logger.warning(
                f"g.node.forest from {from_alias} is not the registry "
                f"({self.registry_alias}) — witnessed, not projected"
            )
            return None
        return lambda db: self.project_forest(db, forest)

    def persist_v000(
        self, from_alias: str, time_received: datetime, forest: GNodeForest000
    ) -> MessagePersistenceInfo:
        return MessagePersistenceInfo(
            id=default_message_id(from_alias, "g.node.forest", time_received),
            created_at=None,
            additional_db_operations=self._fanout_if_registry(from_alias, forest),
        )

    def persist_v001(
        self, from_alias: str, time_received: datetime, forest: GNodeForest001
    ) -> MessagePersistenceInfo:
        # SendTimeMs is the registry's clock at forest assembly — the
        # message's created_at, per the sender-time standard. Optional in 001.
        created_at = (
            datetime.fromtimestamp(forest.send_time_ms / 1000, UTC)
            if forest.send_time_ms is not None
            else None
        )
        return MessagePersistenceInfo(
            id=default_message_id(from_alias, "g.node.forest", time_received),
            created_at=created_at,
            additional_db_operations=self._fanout_if_registry(from_alias, forest),
        )

    def persist_v002(
        self, from_alias: str, time_received: datetime, forest: GNodeForest
    ) -> MessagePersistenceInfo:
        # SendTimeMs is required in 002, so created_at is always the
        # sender's clock.
        return MessagePersistenceInfo(
            id=default_message_id(from_alias, "g.node.forest", time_received),
            created_at=datetime.fromtimestamp(forest.send_time_ms / 1000, UTC),
            additional_db_operations=self._fanout_if_registry(from_alias, forest),
        )

    def project_forest(self, db: Session, forest: AnyForest) -> None:
        """Upsert a forest's nodes + edges into gw_data. Shared by the live
        broadcast fan-out and the read-API bootstrap (forest_bootstrap).

        The forest's send time rides into every row it writes (`sent_at`),
        and a write whose send time is older than the row's stored one is
        skipped — an out-of-order assertion (e.g. the one-time bootstrap
        response landing after a newer live broadcast) cannot regress the
        projection. Equal send times pass, keeping replays idempotent."""
        sent_at = None
        send_time_ms = getattr(forest, "send_time_ms", None)
        if send_time_ms is not None:
            sent_at = datetime.fromtimestamp(send_time_ms / 1000, UTC)
        for node in forest.nodes:
            self._upsert_node(db, node, sent_at)
        db.flush()  # edges FK the nodes
        for edge in forest.edges:
            self._upsert_edge(db, edge, sent_at)

    def _upsert_node(self, db: Session, gt: GNodeGt, sent_at: datetime | None) -> None:
        node_id = uuid.UUID(gt.g_node_id)
        # The registry's opaque location identity, stored verbatim — gw_data
        # holds no position content, so there is nothing local to resolve
        # against.
        position_point_id = (
            uuid.UUID(gt.position_point_id) if gt.position_point_id else None
        )

        row = db.get(GNodeSql, node_id)
        if row is None:
            row = GNodeSql(id=node_id)
            db.add(row)
        elif sent_at is not None and row.sent_at is not None and sent_at < row.sent_at:
            self.logger.warning(
                f"g_node {gt.alias}: send time {sent_at.isoformat()} is older "
                f"than the row's {row.sent_at.isoformat()} — write skipped"
            )
            return
        row.alias = gt.alias
        row.prev_alias = gt.prev_alias
        row.base_class = DbBaseGNodeClass(gt.base_class.value)
        row.g_node_class = gt.g_node_class
        row.status = DbGNodeStatus(gt.status.value)
        row.position_point_id = position_point_id
        row.display_name = gt.display_name
        if sent_at is not None:
            row.sent_at = sent_at

    def _upsert_edge(
        self, db: Session, gt: ConnectivityEdgeGt, sent_at: datetime | None
    ) -> None:
        edge_id = uuid.UUID(gt.id)
        from_id = uuid.UUID(gt.from_g_node_id)
        to_id = uuid.UUID(gt.to_g_node_id)

        missing = [x for x in (from_id, to_id) if db.get(GNodeSql, x) is None]
        if missing:
            # An endpoint outside this broadcast's subtrees hasn't been
            # projected yet; a forest carrying it converges the edge later.
            self.logger.warning(
                f"connectivity edge {gt.id}: endpoint g_node(s) "
                f"{[str(m) for m in missing]} not in gw_data — edge skipped"
            )
            return

        row = db.get(ConnectivityEdgeSql, edge_id)
        if (
            row is not None
            and sent_at is not None
            and row.sent_at is not None
            and sent_at < row.sent_at
        ):
            self.logger.warning(
                f"connectivity edge {gt.id}: send time {sent_at.isoformat()} "
                f"is older than the row's {row.sent_at.isoformat()} — write "
                "skipped"
            )
            return
        if row is None:
            # An edge's id is immutable for its (from, to) pair — lifecycle
            # rides Status on the same id, and the registry has no command
            # that re-creates a pair under a new id. A conflicting pair row
            # is an anomaly to surface, never an identity change to absorb.
            pair_row = (
                db
                .query(ConnectivityEdgeSql)
                .filter_by(from_g_node_id=from_id, to_g_node_id=to_id)
                .one_or_none()
            )
            if pair_row is not None:
                self.logger.warning(
                    f"connectivity edge {gt.id}: pair "
                    f"({gt.from_g_node_id}, {gt.to_g_node_id}) already held "
                    f"by edge {pair_row.id} — edge ids are immutable per "
                    "pair; skipping, reconcile by hand"
                )
                return
            row = ConnectivityEdgeSql(
                id=edge_id, from_g_node_id=from_id, to_g_node_id=to_id
            )
            db.add(row)
        row.status = DbGNodeStatus(gt.status.value)
        if sent_at is not None:
            row.sent_at = sent_at
