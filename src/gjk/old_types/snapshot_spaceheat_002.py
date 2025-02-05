"""Type snapshot.spaceheat, version 002"""

from typing import List, Literal

from gw.named_types import GwBase

from gjk.named_types.machine_states import MachineStates
from gjk.named_types.single_reading import SingleReading
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UUID4Str,
)


class SnapshotSpaceheat002(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    snapshot_time_unix_ms: UTCMilliseconds
    latest_reading_list: List[SingleReading]
    latest_state_list: List[MachineStates]
    type_name: Literal["snapshot.spaceheat"] = "snapshot.spaceheat"
    version: Literal["002"] = "002"
