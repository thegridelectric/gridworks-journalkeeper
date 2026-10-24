"""Which reading_channels row each channel of a layout or a report is.

A row is one (name, definition) of a terminal asset, where the definition
is the unit, unit type and channel type. Its `channel_id` is the layout's
channel Id for the pair (data, derived and synth channels), the lineage
key a renamed channel's rows share; a pseudo channel has none. The row's
primary key is a surrogate.

A report names its channels by name only, so the layout in force at the
report's time says which definition a name means: the newest layout.lite
message from the scada at or before the report. The terminal asset's row
in `layouts` is the live projection of that same message; the resolver
reads it as a cache that must agree, and logs a row that names another
message (a layout the live path missed and a back-fill brought).

The reading then goes to the row of that (name, definition) whose era
contains the report's time (`reading_channel_eras`). A report from before
the first layout the journal has from its scada has no layout in force
and routes by name alone through the same era rule.

The row a name resolves to holds the layout's Id for that name as its
`channel_id` (a pseudo row holds none); the resolution says what the
layout declared so the report persistor can check that and tally a
disagreement.
"""

import logging
import uuid
from collections.abc import Iterator
from datetime import datetime
from typing import NamedTuple

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


class KnownLayout(NamedTuple):
    """The newest layout.lite message seen from one scada: a later report
    only looks for a layout between this one's time and its own. In-process
    cache state, not durable data: no sema word retires it."""

    message_id: uuid.UUID
    timestamp: datetime
    payload: dict


class Resolution(NamedTuple):
    """Where a report's channel names go. `row_ids`: name -> the
    reading_channels row id. `declared_ids`: name -> the channel Id the
    layout in force declares (None for a pseudo channel); empty when no
    layout is in force and the names routed by the era rule alone.
    In-process routing state, not durable data: no sema word retires it."""

    row_ids: dict[str, uuid.UUID]
    declared_ids: dict[str, uuid.UUID | None]


class ChannelResolver:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.codec = SemaCodec()
        # layout message id -> the rows that layout declares. Layouts are
        # rare messages, so the cache stays small across a back-fill.
        self.rows_by_layout: dict[uuid.UUID, list[ReadingChannelSql]] = {}
        # scada alias -> the newest layout.lite message seen from it
        self.newest_by_alias: dict[str, KnownLayout] = {}
        # layouts rows already reported as naming another message
        self.stale_rows_logged: set[uuid.UUID] = set()

    def layout_in_force(
        self, db: Session, from_alias: str, terminal_asset_alias: str, t: datetime
    ) -> tuple[uuid.UUID, dict] | None:
        """The (message id, payload) of the newest layout.lite from the scada
        at or before t, if any."""
        query = db.query(MessageSql).filter(
            MessageSql.from_alias == from_alias,
            MessageSql.message_type_name == LayoutLite.type_name_value(),
            MessageSql.timestamp <= t,
        )
        known = self.newest_by_alias.get(from_alias)
        if known is not None and known.timestamp <= t:
            query = query.filter(MessageSql.timestamp > known.timestamp)
        msg = query.order_by(MessageSql.timestamp.desc()).first()
        if isinstance(msg, MessageSql):
            found = KnownLayout(msg.id, msg.timestamp, msg.payload)
        elif known is not None and known.timestamp <= t:
            found = known
        else:
            return None
        if known is None or found.timestamp >= known.timestamp:
            self.newest_by_alias[from_alias] = found
        self.check_projection(db, terminal_asset_alias, found, t)
        return found.message_id, found.payload

    def check_projection(
        self, db: Session, terminal_asset_alias: str, found: KnownLayout, t: datetime
    ) -> None:
        """The `layouts` row is the live projection of the newest layout. A row
        sent at or before t that names another message is stale, logged once
        per row."""
        row = (
            db
            .query(LayoutSql)
            .filter(LayoutSql.terminal_asset_alias == terminal_asset_alias)
            .one_or_none()
        )
        if (
            not isinstance(row, LayoutSql)
            or row.message_id is None
            or row.sent_at > t
            or row.message_id == found.message_id
            or row.message_id in self.stale_rows_logged
        ):
            return
        self.stale_rows_logged.add(row.message_id)
        self.logger.warning(
            f"layouts row for {terminal_asset_alias} is message {row.message_id} "
            f"sent {row.sent_at.isoformat()}; the newest layout.lite at "
            f"{t.isoformat()} is {found.message_id} sent {found.timestamp.isoformat()}"
        )

    def resolve(
        self,
        db: Session,
        from_alias: str,
        terminal_asset_alias: str,
        rows: list[ReadingChannelSql],
        t: datetime,
    ) -> Resolution:
        """Channel name -> row id for a report at time t, with what the layout
        in force declared each name to be."""
        found = self.layout_in_force(db, from_alias, terminal_asset_alias, t)
        if found is None:
            return Resolution(channel_ids_at(rows, t), {})
        message_id, payload = found
        if message_id not in self.rows_by_layout:
            layout = self.codec.from_dict(payload, auto_upgrade=False)
            assert isinstance(layout, MODERN_LAYOUTS)
            self.rows_by_layout[message_id] = list(
                declared_rows(layout, terminal_asset_alias)
            )
        row_ids: dict[str, uuid.UUID] = {}
        declared_ids: dict[str, uuid.UUID | None] = {}
        for declared in self.rows_by_layout[message_id]:
            row_ids.update(channel_ids_at(rows_of(declared, rows), t))
            declared_ids[declared.name] = declared.channel_id
        return Resolution(row_ids, declared_ids)
