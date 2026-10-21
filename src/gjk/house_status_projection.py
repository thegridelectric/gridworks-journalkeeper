"""The house operating status projection: one current status row per house.

``gridworks.house_operating_status`` holds, for each TerminalAsset, the
latest ``gw.house.operating.status`` the journal has for it, verbatim,
keyed on the TerminalAsset GNodeId. The word is sent on change only, so
a reader wants the latest row by key and never a window over messages.

Two writers, told apart by the row's ``source``. A scada that sends the
word writes a ``scada`` row, guarded on the word's ``CreatedMs`` so an
older status never overwrites a newer one. A house whose scada does not
send the word yet (the old scada code) gets a ``derived`` row built from
its current layout and newest snapshot, through the word's own class so
the row is a valid instance; a derived row never overwrites a scada row.
Retiring the old scada code deletes the derivation.

The projection is current state, so it runs on live messages only
(``MessagePersistenceInfo.live_only_db_operations``) and is rebuilt from
the journal by ``python -m gjk.rebuild_house_status``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from gw_data.db.models import GNodeSql, HouseOperatingStatusSql, LayoutSql, MessageSql
from sqlalchemy.orm import Session

from gjk.layouts_projection import terminal_asset_alias
from gjk.sema.codec import SemaCodec
from gjk.sema.enums import (
    Gw1MainAutoState,
    Gw1ServiceMode,
    Gw1SystemMode,
    GwDispatchRefusalReason,
    GwStandbyPosture,
    GwTopState,
    TaValidationState,
)
from gjk.sema.types import GwHouseOperatingStatus, LayoutLite, SnapshotSpaceheat
from gjk.sema.types.old_versions.layout_lite_011 import LayoutLite011

SOURCE_SCADA = "scada"
SOURCE_DERIVED = "derived"
SNAPSHOT_SPACEHEAT = "snapshot.spaceheat"
TOP_STATE_ENUM = "top.state"
MAIN_AUTO_STATE_ENUM = "gw1.main.auto.state"

# The layout versions that say the system mode, which the derivation needs.
type ModeLayout = LayoutLite011 | LayoutLite


def snapshot_state(snapshot: SnapshotSpaceheat | None, state_enum: str) -> str | None:
    """The snapshot's latest value of one state machine, by its enum name."""
    if snapshot is None:
        return None
    return next(
        (s.state for s in snapshot.latest_state_list if s.state_enum == state_enum),
        None,
    )


def derived_status(
    layout: ModeLayout, snapshot: SnapshotSpaceheat | None
) -> GwHouseOperatingStatus:
    """The operating status of a house on the old scada code, from what it
    does send. The old code never refuses a contract and checks no channel
    freshness, so AcceptsDispatch follows the top state and the system mode
    alone and ScadaBlind is false. It has no deed, so ValidationState is the
    enum's UnValidated. The record's time is the newer of its two sources."""
    standby = layout.system_mode == Gw1SystemMode.Standby
    monitor_only = layout.system_mode == Gw1SystemMode.MonitorOnly
    top_state_value = snapshot_state(snapshot, TOP_STATE_ENUM)
    top_state = (
        GwTopState(top_state_value)
        if top_state_value in GwTopState.values()
        else GwTopState.Auto
    )
    refusal: GwDispatchRefusalReason | None = None
    if standby or monitor_only:
        refusal = GwDispatchRefusalReason.OperatorHold
    elif top_state == GwTopState.Admin:
        refusal = GwDispatchRefusalReason.InAdmin
    created_ms = layout.message_created_ms
    if snapshot is not None:
        created_ms = max(created_ms, snapshot.snapshot_time_unix_ms)
    return GwHouseOperatingStatus(
        scada_alias=layout.from_g_node_alias,
        validation_state=TaValidationState.UnValidated,
        standby=standby,
        standby_posture=GwStandbyPosture.MonitorOnly
        if monitor_only
        else GwStandbyPosture.NoHeatingOrCooling,
        seasonal_storage_mode=layout.seasonal_storage_mode,
        service_mode=Gw1ServiceMode.Heating,
        accepts_dispatch=refusal is None,
        dispatch_refusal_reason=refusal,
        top_state=top_state,
        scada_blind=False,
        ltn_dispatching=snapshot_state(snapshot, MAIN_AUTO_STATE_ENUM)
        == Gw1MainAutoState.LeafTransactiveNode.value,
        created_ms=created_ms,
    )


class HouseStatusProjection:
    def __init__(self, logger):
        self.logger = logger
        self.codec = SemaCodec()

    def terminal_asset(self, db: Session, ta_alias: str) -> GNodeSql | None:
        return db.query(GNodeSql).filter(GNodeSql.alias == ta_alias).one_or_none()

    def write(
        self,
        db: Session,
        row: HouseOperatingStatusSql | None,
        ta: GNodeSql,
        status: GwHouseOperatingStatus,
        source: str,
        message_id: uuid.UUID | None,
    ) -> None:
        if row is None:
            row = HouseOperatingStatusSql(ta_g_node_id=ta.id)
            db.add(row)
        row.terminal_asset_alias = ta.alias
        row.scada_alias = status.scada_alias
        row.source = source
        row.type_name = status.type_name
        row.version = status.version
        row.payload = status.to_dict()
        row.message_id = message_id
        row.created_at = datetime.fromtimestamp(status.created_ms / 1000, UTC)

    def project_reported(
        self,
        db: Session,
        from_alias: str,
        status: GwHouseOperatingStatus,
        message_id: str,
    ) -> None:
        """Upsert the status a scada sent as its house's current status."""
        ta_alias = terminal_asset_alias(status.scada_alias)
        ta = self.terminal_asset(db, ta_alias)
        if ta is None:
            self.logger.warning(
                f"gw.house.operating.status from {from_alias}: no g_nodes row for {ta_alias} — not projected"
            )
            return
        created_at = datetime.fromtimestamp(status.created_ms / 1000, UTC)
        row = db.get(HouseOperatingStatusSql, ta.id)
        if (
            row is not None
            and row.source == SOURCE_SCADA
            and created_at < row.created_at
        ):
            self.logger.warning(
                f"gw.house.operating.status from {from_alias}: created {created_at.isoformat()} is older "
                f"than the row's {row.created_at.isoformat()} — write skipped"
            )
            return
        self.write(db, row, ta, status, SOURCE_SCADA, uuid.UUID(message_id))

    def newest_snapshot(
        self, db: Session, scada_alias: str
    ) -> SnapshotSpaceheat | None:
        msg = (
            db
            .query(MessageSql)
            .filter(
                MessageSql.from_alias == scada_alias,
                MessageSql.message_type_name == SNAPSHOT_SPACEHEAT,
            )
            .order_by(MessageSql.timestamp.desc())
            .first()
        )
        if msg is None:
            return None
        snapshot = self.codec.from_dict(msg.payload)
        assert isinstance(snapshot, SnapshotSpaceheat)
        return snapshot

    def derive(self, db: Session, ta_alias: str) -> bool:
        """Write the derived status of a house whose scada does not send the
        word, from its current layout row and newest journaled snapshot.
        True when a row was written."""
        ta = self.terminal_asset(db, ta_alias)
        if ta is None:
            return False
        row = db.get(HouseOperatingStatusSql, ta.id)
        if row is not None and row.source == SOURCE_SCADA:
            return False
        layout_row = db.get(LayoutSql, ta.id)
        if layout_row is None:
            return False
        layout = self.codec.from_dict(layout_row.payload, auto_upgrade=False)
        if not isinstance(layout, (LayoutLite011, LayoutLite)):
            return False
        status = derived_status(
            layout, self.newest_snapshot(db, layout.from_g_node_alias)
        )
        self.write(db, row, ta, status, SOURCE_DERIVED, None)
        return True
