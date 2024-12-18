"""Type snapshot.spaceheat, version 000"""

from typing import Literal

from gw.named_types import GwBase

from gjk.old_types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat
from gjk.property_format import (
    LeftRightDot,
    UUID4Str,
)


class SnapshotSpaceheat000(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    snapshot: TelemetrySnapshotSpaceheat
    type_name: Literal["snapshot.spaceheat"] = "snapshot.spaceheat"
    version: Literal["000"] = "000"
