"""Which reading_channels row each channel of a layout or a report is.

A row is one (name, definition) of a terminal asset, where the definition
is the unit, unit type and channel type. Its `channel_id` is the layout's
channel Id for the pair (data, derived and synth channels), the lineage
key a renamed channel's rows share; a pseudo channel has none. The row's
primary key is a surrogate.

A report names its channels by name only, so the layout in force at the
report's time says which definition a name means:

- the terminal asset's row in `layouts` when the report is at or after its
  send time (the live case: that row is the newest layout the journal has
  seen), else
- the newest layout.lite message from the scada at or before the report
  (the back-fill case).

The reading then goes to the row of that (name, definition) whose era
contains the report's time (`reading_channel_eras`). A report from before
the first layout the journal has from its scada has no layout in force
and routes by name alone through the same era rule.
"""

import uuid
from collections.abc import Iterator
from datetime import datetime

from gw_data.db.models import LayoutSql, MessageSql, ReadingChannelSql
from sqlalchemy.orm import Session

from gjk.message_persistence_info import pseudo_channel_id
from gjk.pseudo_channels import (
    MODERN_LAYOUTS,
    SYNTH_ERA_LAYOUTS,
    ModernLayout,
    PseudoChannel,
    SynthEraLayout,
    get_pseudo_channels,
)
from gjk.reading_channel_eras import channel_ids_at
from gjk.sema import SemaCodec
from gjk.sema.enums import Gw1Unit, SpaceheatTelemetryName
from gjk.sema.types import DataChannelGt, DerivedChannelGt, LayoutLite, SynthChannelGt
from gjk.sema.types.old_versions.data_channel_gt_001 import DataChannelGt001
from gjk.sema.types.old_versions.derived_channel_gt_000 import DerivedChannelGt000
from gjk.sema.types.old_versions.layout_lite_001 import LayoutLite001
from gjk.sema.types.old_versions.layout_lite_002 import LayoutLite002

# The only synth channels that ever appear in report.event readings, present
# from the beginning of the archive. The other synth channels in a layout are
# unreported intermediates and get no reading_channels rows.
REPORTED_SYNTH_CHANNELS = ("required-energy", "usable-energy")

def data_channel_row(dc: DataChannelGt | DataChannelGt001) -> ReadingChannelSql:
    return ReadingChannelSql(
        channel_id=uuid.UUID(dc.id),
        name=dc.name,
        terminal_asset_alias=dc.terminal_asset_alias,
        display_name=dc.display_name,
        unit=dc.telemetry_name,
        unit_type=SpaceheatTelemetryName.enum_name(),
        channel_type=DataChannelGt.type_name_value(),
    )


def derived_channel_row(
    dc: DerivedChannelGt | DerivedChannelGt000,
) -> ReadingChannelSql:
    return ReadingChannelSql(
        channel_id=uuid.UUID(dc.id),
        name=dc.name,
        terminal_asset_alias=dc.terminal_asset_alias,
        display_name=dc.display_name,
        unit=dc.output_unit if dc.output_unit is not None else "Unknown",
        unit_type=Gw1Unit.enum_name(),
        channel_type=DerivedChannelGt.type_name_value(),
    )


def synth_channel_row(sc: SynthChannelGt) -> ReadingChannelSql:
    return ReadingChannelSql(
        channel_id=uuid.UUID(sc.id),
        name=sc.name,
        terminal_asset_alias=sc.terminal_asset_alias,
        display_name=sc.display_name,
        unit=sc.telemetry_name,
        unit_type=SpaceheatTelemetryName.enum_name(),
        channel_type=SynthChannelGt.type_name_value(),
    )


def pseudo_channel_row(
    pc: PseudoChannel, terminal_asset_alias: str
) -> ReadingChannelSql:
    return ReadingChannelSql(
        id=pseudo_channel_id(terminal_asset_alias, pc.name, pc.unit_type, pc.unit),
        name=pc.name,
        terminal_asset_alias=terminal_asset_alias,
        display_name=pc.display_name,
        unit=pc.unit,
        unit_type=pc.unit_type,
        channel_type=PseudoChannel.CHANNEL_TYPE,
    )


def reported_synth_channels(layout: SynthEraLayout) -> list[SynthChannelGt]:
    if isinstance(layout, LayoutLite001):
        declared = []
    elif isinstance(layout, LayoutLite002):
        declared = layout.synth_channels or []
    else:
        declared = layout.synth_channels
    return [sc for sc in declared if sc.name in REPORTED_SYNTH_CHANNELS]


def declared_rows(
    layout: ModernLayout, terminal_asset_alias: str
) -> Iterator[ReadingChannelSql]:
    """Every channel the layout declares, as the row it would be."""
    for dc in layout.data_channels:
        yield data_channel_row(dc)
    if isinstance(layout, SYNTH_ERA_LAYOUTS):
        for sc in reported_synth_channels(layout):
            yield synth_channel_row(sc)
    else:
        for dc in layout.derived_channels:
            yield derived_channel_row(dc)
    for pc in get_pseudo_channels(layout):
        yield pseudo_channel_row(pc, terminal_asset_alias)


def same_definition(a: ReadingChannelSql, b: ReadingChannelSql) -> bool:
    return (
        a.name == b.name
        and a.unit == b.unit
        and a.unit_type == b.unit_type
        and a.channel_type == b.channel_type
    )


def rows_of(
    declared: ReadingChannelSql, rows: list[ReadingChannelSql]
) -> list[ReadingChannelSql]:
    """The rows (any era) that are the declared channel: same name, same
    definition."""
    return [r for r in rows if r.name == declared.name and same_definition(r, declared)]


class ChannelResolver:
    def __init__(self):
        self.codec = SemaCodec()
        # layout message id -> the rows that layout declares. Layouts are
        # rare messages, so the cache stays small across a back-fill.
        self.rows_by_layout: dict[uuid.UUID, list[ReadingChannelSql]] = {}

    def layout_in_force(
        self, db: Session, from_alias: str, terminal_asset_alias: str, t: datetime
    ) -> tuple[uuid.UUID, dict] | None:
        """The (message id, payload) of the layout in force at t, if any."""
        current = (
            db
            .query(LayoutSql)
            .filter(LayoutSql.terminal_asset_alias == terminal_asset_alias)
            .one_or_none()
        )
        if (
            isinstance(current, LayoutSql)
            and current.message_id is not None
            and current.sent_at <= t
        ):
            return current.message_id, current.payload
        msg = (
            db
            .query(MessageSql)
            .filter(
                MessageSql.from_alias == from_alias,
                MessageSql.message_type_name == LayoutLite.type_name_value(),
                MessageSql.timestamp <= t,
            )
            .order_by(MessageSql.timestamp.desc())
            .first()
        )
        if not isinstance(msg, MessageSql):
            return None
        return msg.id, msg.payload

    def resolve(
        self,
        db: Session,
        from_alias: str,
        terminal_asset_alias: str,
        rows: list[ReadingChannelSql],
        t: datetime,
    ) -> dict[str, uuid.UUID]:
        """Channel name -> row id for a report at time t."""
        found = self.layout_in_force(db, from_alias, terminal_asset_alias, t)
        if found is None:
            return channel_ids_at(rows, t)
        message_id, payload = found
        if message_id not in self.rows_by_layout:
            layout = self.codec.from_dict(payload, auto_upgrade=False)
            assert isinstance(layout, MODERN_LAYOUTS)
            self.rows_by_layout[message_id] = list(
                declared_rows(layout, terminal_asset_alias)
            )
        by_name: dict[str, uuid.UUID] = {}
        for declared in self.rows_by_layout[message_id]:
            by_name.update(channel_ids_at(rows_of(declared, rows), t))
        return by_name
