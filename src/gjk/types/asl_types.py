"""List of all the types used by the actor."""

from typing import List, no_type_check

from gjk.types.batched_readings import BatchedReadings
from gjk.types.channel_readings import ChannelReadings
from gjk.types.data_channel_gt import DataChannelGt
from gjk.types.dispatch import Dispatch
from gjk.types.fsm_atomic_report import FsmAtomicReport
from gjk.types.fsm_full_report import FsmFullReport
from gjk.types.gridworks_event_gt_sh_status import GridworksEventGtShStatus
from gjk.types.gridworks_event_snapshot_spaceheat import (
    GridworksEventSnapshotSpaceheat,
)
from gjk.types.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatus
from gjk.types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from gjk.types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus
from gjk.types.gt_sh_status import GtShStatus
from gjk.types.gw_base import GwBase
from gjk.types.heartbeat_a import HeartbeatA
from gjk.types.keyparam_change_log import KeyparamChangeLog
from gjk.types.power import Power
from gjk.types.power_watts import PowerWatts
from gjk.types.snapshot_spaceheat import SnapshotSpaceheat
from gjk.types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat

TypeByName: dict[str, GwBase] = {}


@no_type_check
def types() -> List[Power]:
    return [
        Dispatch,  # special non-json serialization
        Power,  # special non-json serialization
        BatchedReadings,
        ChannelReadings,
        DataChannelGt,
        FsmAtomicReport,
        FsmFullReport,
        GridworksEventGtShStatus,
        GridworksEventSnapshotSpaceheat,
        GtShBooleanactuatorCmdStatus,
        GtShMultipurposeTelemetryStatus,
        GtShSimpleTelemetryStatus,
        GtShStatus,
        HeartbeatA,
        KeyparamChangeLog,
        PowerWatts,
        SnapshotSpaceheat,
        TelemetrySnapshotSpaceheat,
    ]


for t in types():
    try:
        TypeByName[t.type_name_value()] = t
    except:
        print(f"Problem w {t}")
