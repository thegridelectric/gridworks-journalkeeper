"""Type snapshot.spaceheat, version 001"""

from typing import List, Literal

from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UUID4Str,
)
from gjk.types.gw_base import GwBase
from gjk.types.single_reading import SingleReading


class SnapshotSpaceheat(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    snapshot_time_unix_ms: UTCMilliseconds
    latest_reading_list: List[SingleReading]
    type_name: Literal["snapshot.spaceheat"] = "snapshot.spaceheat"
    version: Literal["001"] = "001"
