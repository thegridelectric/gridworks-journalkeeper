"""Type snapshot.spaceheat, version 003"""

from typing import List, Literal

from gw.named_types import GwBase

from gjk.named_types.single_machine_state import SingleMachineState
from gjk.named_types.single_reading import SingleReading
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UUID4Str,
)


class SnapshotSpaceheat(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    snapshot_time_unix_ms: UTCMilliseconds
    latest_reading_list: List[SingleReading]
    latest_state_list: List[SingleMachineState]
    type_name: Literal["snapshot.spaceheat"] = "snapshot.spaceheat"
    version: str = "003"
