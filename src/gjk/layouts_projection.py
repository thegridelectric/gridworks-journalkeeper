"""The layouts projection: one current layout row per terminal asset.

``gridworks.layouts`` holds, for each TerminalAsset, the latest layout
word the journal has seen for it, verbatim, keyed on the TerminalAsset
GNodeId. Readers ask for a house's layout by key instead of scanning the
messages hypertable for the newest layout message.

The row is written the way ``g_nodes`` is written from the registry's
forest: an upsert on the immutable key, with the sender's clock as the
row's ``sent_at`` and a write whose send time is older than the row's
skipped. The guard compares send times only, so a house that runs a newer
layout word for a window and goes back follows the house. The projection
is current state, so it runs on live messages only; a persistent-store
replay never touches it (``MessagePersistenceInfo.live_only_db_operations``).

A row the registry wrote is not overwritten by a scada's message; a scada
message whose payload differs is logged as a mismatch. Until the registry
sends layouts every row is scada-written and the rule has nothing to do.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from gw_data.db.models import GNodeSql, LayoutSql
from sqlalchemy.orm import Session

from gjk.pseudo_channels import ModernLayout


def terminal_asset_alias(scada_alias: str) -> str:
    """The TerminalAsset alias a scada's alias names: `<house>.scada` -> `<house>.ta`."""
    return scada_alias.split(".scada")[0] + ".ta"


class LayoutsProjection:
    def __init__(self, logger, registry_alias: str | None = None):
        self.logger = logger
        # The sender whose rows a scada may not overwrite. None until the
        # terminalasset registry sends layouts.
        self.registry_alias = registry_alias

    def project(self, db: Session, from_alias: str, layout: ModernLayout) -> None:
        """Upsert the scada's layout.lite as its terminal asset's current layout."""
        ta_alias = terminal_asset_alias(layout.from_g_node_alias)
        ta = db.query(GNodeSql).filter(GNodeSql.alias == ta_alias).one_or_none()
        if ta is None:
            self.logger.warning(
                f"layout.lite from {from_alias}: no g_nodes row for {ta_alias} — not projected"
            )
            return
        sent_at = datetime.fromtimestamp(layout.message_created_ms / 1000, UTC)
        payload = layout.to_dict()

        row = db.get(LayoutSql, ta.id)
        if row is None:
            row = LayoutSql(ta_g_node_id=ta.id)
            db.add(row)
        elif self.registry_alias is not None and row.from_alias == self.registry_alias:
            if row.payload != payload:
                self.logger.warning(
                    f"layout.lite from {from_alias} differs from the registry's layout for {ta_alias} — mismatch, row kept"
                )
            return
        elif sent_at < row.sent_at:
            self.logger.warning(
                f"layout.lite from {from_alias}: send time {sent_at.isoformat()} is older "
                f"than the row's {row.sent_at.isoformat()} — write skipped"
            )
            return
        row.terminal_asset_alias = ta_alias
        row.from_alias = from_alias
        row.type_name = layout.type_name
        row.version = layout.version
        row.payload = payload
        row.message_id = uuid.UUID(layout.message_id)
        row.sent_at = sent_at
