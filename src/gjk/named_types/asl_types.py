"""List of all the types used by the actor."""

from typing import Dict, List, no_type_check

from gw.named_types import GwBase

from gjk.named_types.channel_config import ChannelConfig
from gjk.named_types.channel_readings import ChannelReadings
from gjk.named_types.data_channel_gt import DataChannelGt
from gjk.named_types.fsm_atomic_report import FsmAtomicReport
from gjk.named_types.fsm_event import FsmEvent
from gjk.named_types.fsm_full_report import FsmFullReport
from gjk.named_types.gridworks_event_problem import GridworksEventProblem
from gjk.named_types.heartbeat_a import HeartbeatA
from gjk.named_types.keyparam_change_log import KeyparamChangeLog
from gjk.named_types.layout_event import LayoutEvent
from gjk.named_types.layout_lite import LayoutLite
from gjk.named_types.machine_states import MachineStates
from gjk.named_types.my_channels import MyChannels
from gjk.named_types.my_channels_event import MyChannelsEvent
from gjk.named_types.pico_flow_module_component_gt import PicoFlowModuleComponentGt
from gjk.named_types.pico_tank_module_component_gt import PicoTankModuleComponentGt
from gjk.named_types.power_watts import PowerWatts
from gjk.named_types.report import Report
from gjk.named_types.report_event import ReportEvent
from gjk.named_types.snapshot_spaceheat import SnapshotSpaceheat
from gjk.named_types.ticklist_hall import TicklistHall
from gjk.named_types.ticklist_hall_report import TicklistHallReport
from gjk.named_types.ticklist_reed import TicklistReed
from gjk.named_types.ticklist_reed_report import TicklistReedReport
from gjk.old_types import GridworksEventSnapshotSpaceheat
from gjk.old_types.batched_readings import BatchedReadings
from gjk.old_types.channel_readings_000 import ChannelReadings000
from gjk.old_types.channel_readings_001 import ChannelReadings001
from gjk.old_types.gridworks_event_gt_sh_status import GridworksEventGtShStatus
from gjk.old_types.gridworks_event_report import GridworksEventReport
from gjk.old_types.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatus
from gjk.old_types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from gjk.old_types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus
from gjk.old_types.gt_sh_status import GtShStatus
from gjk.old_types.report_000 import Report000
from gjk.old_types.snapshot_spaceheat_000 import SnapshotSpaceheat000
from gjk.old_types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat

TypeByName: Dict[str, GwBase] = {}


@no_type_check
def types() -> List[GwBase]:
    return [
        BatchedReadings,
        ChannelReadings000,
        ChannelReadings001,
        GridworksEventGtShStatus,
        GridworksEventReport,
        GridworksEventSnapshotSpaceheat,
        GtShBooleanactuatorCmdStatus,
        GtShMultipurposeTelemetryStatus,
        GtShSimpleTelemetryStatus,
        GtShStatus,
        Report000,
        SnapshotSpaceheat000,
        TelemetrySnapshotSpaceheat,
        ChannelConfig,
        ChannelReadings,
        DataChannelGt,
        FsmAtomicReport,
        FsmEvent,
        FsmFullReport,
        GridworksEventProblem,
        HeartbeatA,
        KeyparamChangeLog,
        LayoutEvent,
        LayoutLite,
        MachineStates,
        MyChannels,
        MyChannelsEvent,
        PicoFlowModuleComponentGt,
        PicoTankModuleComponentGt,
        PowerWatts,
        Report,
        ReportEvent,
        SnapshotSpaceheat,
        TicklistHall,
        TicklistHallReport,
        TicklistReed,
        TicklistReedReport,
    ]


for t in types():
    try:
        TypeByName[t.type_name_value()] = t
    except:
        print(f"Problem w {t}")
