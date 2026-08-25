import uuid
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime

from gw_data.db.models import MessageSql, ReadingChannelSql
from sqlalchemy import func
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.reading_channel_eras import forget_channel_rows, load_channel_rows
from gjk.pseudo_channels import (
    DerivedEraLayout,
    ModernLayout,
    PseudoChannel,
    SynthEraLayout,
    get_pseudo_channels,
)
from gjk.sema.enums import Gw1Unit, SpaceheatTelemetryName
from gjk.sema.types import DataChannelGt, DerivedChannelGt, LayoutLite, SynthChannelGt
from gjk.sema.types.old_versions.data_channel_gt_001 import DataChannelGt001
from gjk.sema.types.old_versions.derived_channel_gt_000 import DerivedChannelGt000
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

# layout.lite versions whose channel projection is SynthChannels (007+ carry
# DerivedChannels instead). v001 predates SynthChannels altogether and v002
# carries them optionally; both sync as an empty synth set.
SYNTH_ERA_LAYOUTS = (
    LayoutLite006,
    LayoutLite005,
    LayoutLite004,
    LayoutLite003,
    LayoutLite002,
    LayoutLite001,
)

# The only synth channels that ever appear in report.event readings — present
# from the beginning of the archive, kept as synth channels for the synth
# era. The other synth channels in a layout are unreported intermediates and
# get no reading_channels rows.
REPORTED_SYNTH_CHANNELS = ("required-energy", "usable-energy")


class LayoutLitePersistor:
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "layout.lite"
        # (terminal_asset_alias, channel name) -> era rows added by add-only
        # syncs (an older layout's unit/type differed from the active row).
        # Read by the S3 importer's run summary.
        self.skipped_mismatches: Counter[tuple[str, str]] = Counter()

    class ReadingChannelSyncProcess:
        """Reconcile a TA's active reading_channels rows with one layout.

        The newest layout persisted for the TA is the authority on what is
        active. A layout older than that (a bulk back-fill, a replayed queue)
        runs add-only: it never deactivates an active row, so live channels
        survive an old layout arriving late. A channel it carries that is not
        active in the same definition gets an era row — retired at the
        earliest newer layout's time — so readings from its era attach to a
        row with the right unit (see reading_channel_eras).
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
                layout.message_created_ms / 1000, UTC
            )
            self.terminal_asset_alias = terminal_asset_alias
            self.skipped_mismatches = skipped_mismatches
            self.add_only = False
            self.era_boundary: datetime | None = None

        def reconcile(
            self,
            name: str,
            db_channel: ReadingChannelSql | None,
            matches: bool,
            make_row: Callable[[], ReadingChannelSql],
            mismatch_detail: str,
        ):
            """Apply one layout channel against its active DB row (if any).

            No row: add one. Row with the same unit/type: keep it. Row with a
            different unit/type: deactivate it and add a fresh one. Add-only
            (an older layout): the active row is never touched; whatever this
            layout carries that is not active in the same definition is
            recorded as an era row, since the newest layout has superseded it.
            """
            if db_channel is None:
                if self.add_only:
                    self.add_era_row(name, make_row(), "no active row")
                else:
                    self.new_db_channels.append(make_row())
                return
            if not matches:
                if self.add_only:
                    self.add_era_row(name, make_row(), mismatch_detail)
                else:
                    self.logger.info(
                        f"Found channel {name} for {self.terminal_asset_alias} with mismatched unit/type in DB: {mismatch_detail}"
                    )
                    self.new_db_channels.append(make_row())
                    db_channel.deactivated_date = self.msg_timestamp
            del self.existing_db_channels_by_name[name]

        def add_era_row(self, name: str, row: ReadingChannelSql, mismatch_detail: str):
            """Record an older definition of an active channel as a retired era.

            The era ends at the earliest layout newer than this one. Another
            definition already stamped at that boundary was loaded from an
            even older layout, so its era ends here instead. A row with this
            very definition already present means the era is recorded.
            """
            assert self.era_boundary is not None
            same_name = [r for r in self.all_rows if r.name == name]
            for r in same_name:
                if (
                    r.unit == row.unit
                    and r.unit_type == row.unit_type
                    and r.channel_type == row.channel_type
                ):
                    return
            for r in same_name:
                if r.deactivated_date == self.era_boundary:
                    r.deactivated_date = self.msg_timestamp
            self.logger.info(
                f"Era row for {name} on {self.terminal_asset_alias} retired at {self.era_boundary.isoformat()} ({mismatch_detail})"
            )
            self.skipped_mismatches[(self.terminal_asset_alias, name)] += 1
            row.deactivated_date = self.era_boundary
            self.new_db_channels.append(row)
            self.all_rows.append(row)

        def data_channel_to_db(
            self, dc: DataChannelGt | DataChannelGt001
        ) -> ReadingChannelSql:
            return ReadingChannelSql(
                id=uuid.uuid4(),
                name=dc.name,
                terminal_asset_alias=dc.terminal_asset_alias,
                display_name=dc.display_name,
                unit=dc.telemetry_name,
                unit_type=SpaceheatTelemetryName.enum_name(),
                channel_type=DataChannelGt.type_name_value(),
            )

        def derived_channel_to_db(
            self, dc: DerivedChannelGt | DerivedChannelGt000
        ) -> ReadingChannelSql:
            return ReadingChannelSql(
                id=uuid.uuid4(),
                name=dc.name,
                terminal_asset_alias=dc.terminal_asset_alias,
                display_name=dc.display_name,
                unit=dc.output_unit if dc.output_unit is not None else "Unknown",
                unit_type=Gw1Unit.enum_name(),
                channel_type=DerivedChannelGt.type_name_value(),
            )

        def synth_channel_to_db(self, sc: SynthChannelGt) -> ReadingChannelSql:
            return ReadingChannelSql(
                id=uuid.uuid4(),
                name=sc.name,
                terminal_asset_alias=sc.terminal_asset_alias,
                display_name=sc.display_name,
                unit=sc.telemetry_name,
                unit_type=SpaceheatTelemetryName.enum_name(),
                channel_type=SynthChannelGt.type_name_value(),
            )

        def pseudo_channel_to_db(self, pc: PseudoChannel) -> ReadingChannelSql:
            return ReadingChannelSql(
                id=uuid.uuid4(),
                name=pc.name,
                terminal_asset_alias=self.terminal_asset_alias,
                display_name=pc.display_name,
                unit=pc.unit,
                unit_type=pc.unit_type,
                channel_type=PseudoChannel.CHANNEL_TYPE,
            )

        def sync_data_channels(self):
            for dc in self.layout.data_channels:
                db_channel = self.existing_db_channels_by_name.get(dc.name)
                self.reconcile(
                    dc.name,
                    db_channel,
                    db_channel is not None
                    and db_channel.unit == dc.telemetry_name
                    and db_channel.unit_type == SpaceheatTelemetryName.enum_name()
                    and db_channel.channel_type == DataChannelGt.type_name_value(),
                    lambda dc=dc: self.data_channel_to_db(dc),
                    f"{db_channel and db_channel.channel_type}:{db_channel and db_channel.unit_type}:{db_channel and db_channel.unit}/{dc.telemetry_name}",
                )

        def sync_derived_channels(self, layout: DerivedEraLayout):
            for dc in layout.derived_channels:
                db_channel = self.existing_db_channels_by_name.get(dc.name)
                self.reconcile(
                    dc.name,
                    db_channel,
                    db_channel is not None
                    and db_channel.unit == dc.output_unit
                    and db_channel.unit_type == Gw1Unit.enum_name()
                    and db_channel.channel_type == DerivedChannelGt.type_name_value(),
                    lambda dc=dc: self.derived_channel_to_db(dc),
                    f"{db_channel and db_channel.channel_type}:{db_channel and db_channel.unit_type}:{db_channel and db_channel.unit}/{dc.output_unit}",
                )

        def sync_synth_channels(self, layout: SynthEraLayout):
            # Only the reported synth channels get rows; see
            # REPORTED_SYNTH_CHANNELS.
            if isinstance(layout, LayoutLite001):
                synth_channels = []
            elif isinstance(layout, LayoutLite002):
                synth_channels = layout.synth_channels or []
            else:
                synth_channels = layout.synth_channels
            for sc in synth_channels:
                if sc.name not in REPORTED_SYNTH_CHANNELS:
                    continue
                db_channel = self.existing_db_channels_by_name.get(sc.name)
                self.reconcile(
                    sc.name,
                    db_channel,
                    db_channel is not None
                    and db_channel.unit == sc.telemetry_name
                    and db_channel.unit_type == SpaceheatTelemetryName.enum_name()
                    and db_channel.channel_type == SynthChannelGt.type_name_value(),
                    lambda sc=sc: self.synth_channel_to_db(sc),
                    f"{db_channel and db_channel.channel_type}:{db_channel and db_channel.unit_type}:{db_channel and db_channel.unit}/{sc.telemetry_name}",
                )

        def sync_pseudo_channels(self):
            for pc in get_pseudo_channels(self.layout):
                db_channel = self.existing_db_channels_by_name.get(pc.name)
                self.reconcile(
                    pc.name,
                    db_channel,
                    db_channel is not None
                    and db_channel.unit == pc.unit
                    and db_channel.unit_type == pc.unit_type
                    and db_channel.channel_type == PseudoChannel.CHANNEL_TYPE,
                    lambda pc=pc: self.pseudo_channel_to_db(pc),
                    f"{db_channel and db_channel.channel_type}:{db_channel and db_channel.unit_type}:{db_channel and db_channel.unit}/{pc.unit_type}:{pc.unit}",
                )

        def execute(self):
            self.all_rows = load_channel_rows(self.db, self.terminal_asset_alias)
            self.existing_db_channels_by_name = {
                c.name: c for c in self.all_rows if c.deactivated_date is None
            }

            self.new_db_channels = []

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
            if newest_layout_ts is not None and self.add_only:
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

            # Look at every channel (data, derived/synth, and pseudo)
            #   If it does not exist as active in the database, add it
            #   If it exists with a different unit or unit type, deactivate it and add a new one

            self.sync_data_channels()
            if isinstance(self.layout, SYNTH_ERA_LAYOUTS):
                self.sync_synth_channels(self.layout)
            else:
                self.sync_derived_channels(self.layout)
            self.sync_pseudo_channels()

            if not self.add_only:
                for db_only_channel in self.existing_db_channels_by_name.values():
                    self.logger.info(
                        f"Data channel {db_only_channel.name} for {db_only_channel.terminal_asset_alias} exists only in the database"
                    )
                    db_only_channel.deactivated_date = self.msg_timestamp

            for ch in self.new_db_channels:
                self.db.add(ch)
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
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000, tz=UTC),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

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
        self, from_alias: str, time_received: datetime, layout: LayoutLite
    ):
        return self.persist(from_alias, layout)
