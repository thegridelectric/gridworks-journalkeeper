""" List of all the types used by the actor."""

from typing import Dict
from typing import List
from typing import no_type_check

from gjk.types.batched_readings import BatchedReadings_Maker
from gjk.types.channel_readings import ChannelReadings_Maker
from gjk.types.data_channel_gt import DataChannelGt_Maker
from gjk.types.fsm_atomic_report import FsmAtomicReport_Maker
from gjk.types.fsm_full_report import FsmFullReport_Maker
from gjk.types.gridworks_event_gt_sh_status import GridworksEventGtShStatus_Maker
from gjk.types.gridworks_event_snapshot_spaceheat import (
    GridworksEventSnapshotSpaceheat_Maker,
)
from gjk.types.gt_sh_booleanactuator_cmd_status import (
    GtShBooleanactuatorCmdStatus_Maker,
)
from gjk.types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus_Maker,
)
from gjk.types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus_Maker
from gjk.types.gt_sh_status import GtShStatus_Maker
from gjk.types.heartbeat_a import HeartbeatA_Maker
from gjk.types.keyparam_change_log import KeyparamChangeLog_Maker
from gjk.types.power_watts import PowerWatts_Maker
from gjk.types.snapshot_spaceheat import SnapshotSpaceheat_Maker
from gjk.types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat_Maker


TypeMakerByName: Dict[str, HeartbeatA_Maker] = {}


@no_type_check
def type_makers() -> List[HeartbeatA_Maker]:
    return [
        BatchedReadings_Maker,
        ChannelReadings_Maker,
        DataChannelGt_Maker,
        FsmAtomicReport_Maker,
        FsmFullReport_Maker,
        GridworksEventGtShStatus_Maker,
        GridworksEventSnapshotSpaceheat_Maker,
        GtShBooleanactuatorCmdStatus_Maker,
        GtShMultipurposeTelemetryStatus_Maker,
        GtShSimpleTelemetryStatus_Maker,
        GtShStatus_Maker,
        HeartbeatA_Maker,
        KeyparamChangeLog_Maker,
        PowerWatts_Maker,
        SnapshotSpaceheat_Maker,
        TelemetrySnapshotSpaceheat_Maker,
    ]


for maker in type_makers():
    TypeMakerByName[maker.type_name] = maker
