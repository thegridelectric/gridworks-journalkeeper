import uuid
from collections import Counter
from datetime import UTC, datetime

from gw_data.db.models import MessageSql, ReadingChannelSql
from sqlalchemy import func
from sqlalchemy.orm import Session

from gjk.house_status_projection import HouseStatusProjection
from gjk.layouts_projection import LayoutsProjection, terminal_asset_alias
from gjk.channel_resolver import declared_rows, row_id_for
from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.reading_channel_eras import forget_channel_rows, load_channel_rows
from gjk.pseudo_channels import ModernLayout, layout_created_ms
from gjk.sema.types import LayoutLite
from gjk.sema.types.old_versions.layout_lite_001 import LayoutLite001
from gjk.sema.types.old_versions.layout_lite_002 import LayoutLite002
from gjk.sema.types.old_versions.layout_lite_003 import LayoutLite003
from gjk.sema.types.old_versions.layout_lite_004 import LayoutLite004
from gjk.sema.types.old_versions.layout_lite_005 import LayoutLite005
from gjk.sema.types.old_versions.layout_lite_006 import LayoutLite006
from gjk.sema.types.old_versions.layout_lite_007 import LayoutLite007
from gjk.sema.types.old_versions.layout_lite_008 import LayoutLite008
from gjk.sema.types.old_versions.layout_lite_009 import LayoutLite009
from gjk.sema.types.old_versions.layout_lite_010 import LayoutLite010
from gjk.sema.types.old_versions.layout_lite_011 import LayoutLite011
from gjk.sema.types.old_versions.layout_lite_012 import LayoutLite012


class LayoutLitePersistor:
    def __init__(self, logger, house_status: HouseStatusProjection):
        self.logger = logger
        self.house_status = house_status
        self.target_message_type = "layout.lite"
        self.fanout_on_import = True  # history fan-out; replays welcome
        # (terminal_asset_alias, channel name) -> era rows added by add-only
        # syncs (a channel an older layout declares with no row of its own).
        # Read by the S3 importer's run summary.
        self.skipped_mismatches: Counter[tuple[str, str]] = Counter()
        self.layouts = LayoutsProjection(logger)

    class ReadingChannelSyncProcess:
        """Reconcile a TA's reading_channels rows with one layout.

        A row is the channel the layout's Id names (data, derived and synth
        channels) or, for a pseudo channel, the uuid5 of its definition. The
        newest layout persisted for the TA is the authority on what is
        active: a declared channel with a row has that row active, one with
        no row gets one, and an active row the layout does not declare is
        retired at the layout's time. One row of a name is active at a time,
        so a declared channel retires any other active row of its name.

        A layout older than the newest persisted (a bulk back-fill, a
        replayed queue) runs add-only: it never touches an active row, and a
        declared channel with no row gets one retired at the earliest newer
        layout's time, so readings from its era have a row with the right
        unit (see reading_channel_eras).
        """

        def __init__(
            self,
            logger,
            db: Session,
            layout: ModernLayout,
            from_alias: str,
            terminal_asset_alias: str,
            skipped_mismatches: Counter[tuple[str, str]],
        ):
            self.logger = logger
            self.db = db
            self.layout = layout
            self.from_alias = from_alias
            self.msg_timestamp = datetime.fromtimestamp(
                layout_created_ms(layout) / 1000, UTC
            )
            self.terminal_asset_alias = terminal_asset_alias
            self.skipped_mismatches = skipped_mismatches
            self.add_only = False
            self.era_boundary: datetime | None = None
            self.all_rows: list[ReadingChannelSql] = []
            self.rows_by_id: dict[uuid.UUID, ReadingChannelSql] = {}
            self.active_by_name: dict[str, ReadingChannelSql] = {}
            self.declared_names: set[str] = set()
            self.retired: list[ReadingChannelSql] = []
            self.reactivated: list[ReadingChannelSql] = []
            self.new_rows: list[ReadingChannelSql] = []

        def reconcile(self, row: ReadingChannelSql):
            """Apply one declared channel, as the row it would be, to the rows."""
            self.declared_names.add(row.name)
            row.id = row_id_for(row, self.rows_by_id)
            existing = self.rows_by_id.get(row.id)
            if self.add_only:
                if existing is None:
                    self.add_era_row(row)
                return
            if existing is not None and existing.deactivated_date is None:
                return
            other = self.active_by_name.get(row.name)
            if other is not None:
                self.logger.info(
                    f"Channel {row.name} for {self.terminal_asset_alias}: "
                    f"{other.channel_type}:{other.unit_type}:{other.unit} retired for "
                    f"{row.channel_type}:{row.unit_type}:{row.unit}"
                )
                other.deactivated_date = self.msg_timestamp
                self.retired.append(other)
            if existing is None:
                self.new_rows.append(row)
                self.all_rows.append(row)
                self.rows_by_id[row.id] = row
                self.active_by_name[row.name] = row
            else:
                self.reactivated.append(existing)
                self.active_by_name[row.name] = existing

        def add_era_row(self, row: ReadingChannelSql):
            """Record a channel an older layout declares as a retired era.

            The era ends at the earliest layout newer than this one. A row of
            the name already stamped at that boundary was loaded from an even
            older layout, so its era ends here instead.
            """
            assert self.era_boundary is not None
            for r in self.all_rows:
                if r.name == row.name and r.deactivated_date == self.era_boundary:
                    r.deactivated_date = self.msg_timestamp
            self.logger.info(
                f"Era row for {row.name} on {self.terminal_asset_alias} retired at {self.era_boundary.isoformat()} ({row.channel_type}:{row.unit_type}:{row.unit})"
            )
            self.skipped_mismatches[(self.terminal_asset_alias, row.name)] += 1
            row.deactivated_date = self.era_boundary
            self.new_rows.append(row)
            self.all_rows.append(row)
            self.rows_by_id[row.id] = row

        def execute(self):
            self.all_rows = load_channel_rows(self.db, self.terminal_asset_alias)
            self.rows_by_id = {r.id: r for r in self.all_rows}
            self.active_by_name = {
                r.name: r for r in self.all_rows if r.deactivated_date is None
            }

            # This layout's own messages row is already in the session, so a
            # strictly newer timestamp means a newer layout has been persisted.
            newest_layout_ts = (
                self.db
                .query(func.max(MessageSql.timestamp))
                .filter(
                    MessageSql.from_alias == self.from_alias,
                    MessageSql.message_type_name == LayoutLite.type_name_value(),
                )
                .scalar()
            )
            self.add_only = (
                newest_layout_ts is not None and newest_layout_ts > self.msg_timestamp
            )
            if self.add_only:
                self.era_boundary = (
                    self.db
                    .query(func.min(MessageSql.timestamp))
                    .filter(
                        MessageSql.from_alias == self.from_alias,
                        MessageSql.message_type_name == LayoutLite.type_name_value(),
                        MessageSql.timestamp > self.msg_timestamp,
                    )
                    .scalar()
                )
                assert self.era_boundary is not None
                self.logger.info(
                    f"Layout from {self.msg_timestamp.isoformat()} for {self.terminal_asset_alias} is older than the newest persisted ({newest_layout_ts.isoformat()}): add-only sync, era boundary {self.era_boundary.isoformat()}"
                )

            for row in declared_rows(self.layout, self.terminal_asset_alias):
                self.reconcile(row)

            if not self.add_only:
                for name, row in list(self.active_by_name.items()):
                    if name not in self.declared_names:
                        self.logger.info(
                            f"Channel {name} for {self.terminal_asset_alias} exists only in the database"
                        )
                        row.deactivated_date = self.msg_timestamp
                        self.retired.append(row)

            # Retirements flush first: one row of a name is active at a time,
            # and the rows below take the retired rows' place.
            if self.retired:
                self.db.flush()
            for row in self.reactivated:
                row.deactivated_date = None
            for row in self.new_rows:
                self.db.add(row)
            self.db.flush()
            forget_channel_rows(self.db, self.terminal_asset_alias)

    def sync_reading_channels(
        self,
        db: Session,
        from_alias: str,
        layout: ModernLayout,
    ):
        self.ReadingChannelSyncProcess(
            self.logger,
            db,
            layout,
            from_alias,
            from_alias.split(".scada")[0] + ".ta",
            self.skipped_mismatches,
        ).execute()

    def persist(self, from_alias: str, layout: ModernLayout):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout_created_ms(layout) / 1000, tz=UTC),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
            live_only_db_operations=lambda db: self.project_live(
                db, from_alias, layout
            ),
        )

    def project_live(self, db: Session, from_alias: str, layout: ModernLayout) -> None:
        """The current-state projections a live layout feeds: the layouts row,
        then the derived operating status of a house on the old scada code.
        A scada that sends 013 sends gw.house.operating.status itself, so
        nothing is derived from its layout."""
        self.layouts.project(db, from_alias, layout)
        if isinstance(layout, LayoutLite):
            return
        self.house_status.derive(db, terminal_asset_alias(layout.from_g_node_alias))

    def persist_v001(
        self, from_alias: str, time_received: datetime, layout: LayoutLite001
    ):
        return self.persist(from_alias, layout)

    def persist_v002(
        self, from_alias: str, time_received: datetime, layout: LayoutLite002
    ):
        return self.persist(from_alias, layout)

    def persist_v003(
        self, from_alias: str, time_received: datetime, layout: LayoutLite003
    ):
        return self.persist(from_alias, layout)

    def persist_v004(
        self, from_alias: str, time_received: datetime, layout: LayoutLite004
    ):
        return self.persist(from_alias, layout)

    def persist_v005(
        self, from_alias: str, time_received: datetime, layout: LayoutLite005
    ):
        return self.persist(from_alias, layout)

    def persist_v006(
        self, from_alias: str, time_received: datetime, layout: LayoutLite006
    ):
        return self.persist(from_alias, layout)

    def persist_v007(
        self, from_alias: str, time_received: datetime, layout: LayoutLite007
    ):
        return self.persist(from_alias, layout)

    def persist_v008(
        self, from_alias: str, time_received: datetime, layout: LayoutLite008
    ):
        return self.persist(from_alias, layout)

    def persist_v009(
        self, from_alias: str, time_received: datetime, layout: LayoutLite009
    ):
        return self.persist(from_alias, layout)

    def persist_v010(
        self, from_alias: str, time_received: datetime, layout: LayoutLite010
    ):
        return self.persist(from_alias, layout)

    def persist_v011(
        self, from_alias: str, time_received: datetime, layout: LayoutLite011
    ):
        return self.persist(from_alias, layout)

    def persist_v012(
        self, from_alias: str, time_received: datetime, layout: LayoutLite012
    ):
        return self.persist(from_alias, layout)

    def persist_v013(
        self, from_alias: str, time_received: datetime, layout: LayoutLite
    ):
        return self.persist(from_alias, layout)
