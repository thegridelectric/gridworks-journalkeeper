"""List of all the types used by the actor."""

from typing import Dict, List, no_type_check

from gjk.old_types import GridworksEventSnapshotSpaceheat
from gjk.old_types.batched_readings import BatchedReadings
from gjk.old_types.channel_readings_000 import ChannelReadings000
from gjk.old_types.gridworks_event_gt_sh_status import GridworksEventGtShStatus
from gjk.old_types.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatus
from gjk.old_types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from gjk.old_types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus
from gjk.old_types.gt_sh_status import GtShStatus
from gjk.old_types.snapshot_spaceheat_000 import SnapshotSpaceheat000
from gjk.old_types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat
from gjk.types.channel_readings import ChannelReadings
from gjk.types.data_channel_gt import DataChannelGt
from gjk.types.fsm_atomic_report import FsmAtomicReport
from gjk.types.fsm_event import FsmEvent
from gjk.types.fsm_full_report import FsmFullReport
from gjk.types.gridworks_event_report import GridworksEventReport
from gjk.types.gw_base import GwBase
from gjk.types.heartbeat_a import HeartbeatA
from gjk.types.keyparam_change_log import KeyparamChangeLog
from gjk.types.power_watts import PowerWatts
from gjk.types.report import Report
from gjk.types.snapshot_spaceheat import SnapshotSpaceheat

TypeByName: Dict[str, GwBase] = {}


@no_type_check
def types() -> List[GwBase]:
    return [
        BatchedReadings,
        ChannelReadings000,
        GridworksEventGtShStatus,
        GridworksEventSnapshotSpaceheat,
        GtShBooleanactuatorCmdStatus,
        GtShMultipurposeTelemetryStatus,
        GtShSimpleTelemetryStatus,
        GtShStatus,
        SnapshotSpaceheat000,
        TelemetrySnapshotSpaceheat,
        ChannelReadings,
        DataChannelGt,
        FsmAtomicReport,
        FsmEvent,
        FsmFullReport,
        GridworksEventReport,
        HeartbeatA,
        KeyparamChangeLog,
        PowerWatts,
        Report,
        SnapshotSpaceheat,
    ]


for t in types():
    try:
        TypeByName[t.type_name_value()] = t
    except Exception:
        print(f"Problem w {t}")
