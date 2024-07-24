""" List of all the types used by the actor."""

from typing import Dict
from typing import List
from typing import no_type_check

from gwp.types.batched_readings import BatchedReadings_Maker
from gwp.types.channel_readings import ChannelReadings_Maker
from gwp.types.data_channel_gt import DataChannelGt_Maker
from gwp.types.fsm_atomic_report import FsmAtomicReport_Maker
from gwp.types.fsm_full_report import FsmFullReport_Maker
from gwp.types.gridworks_event_gt_sh_status import GridworksEventGtShStatus_Maker
from gwp.types.gridworks_event_snapshot_spaceheat import (
    GridworksEventSnapshotSpaceheat_Maker,
)
from gwp.types.gt_sh_booleanactuator_cmd_status import (
    GtShBooleanactuatorCmdStatus_Maker,
)
from gwp.types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus_Maker,
)
from gwp.types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus_Maker
from gwp.types.gt_sh_status import GtShStatus_Maker
from gwp.types.heartbeat_a import HeartbeatA_Maker
from gwp.types.keyparam_change_log import KeyparamChangeLog_Maker
from gwp.types.power_watts import PowerWatts_Maker
from gwp.types.snapshot_spaceheat import SnapshotSpaceheat_Maker
from gwp.types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat_Maker


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


def version_by_type_name() -> Dict[str, str]:
    """
    Returns:
        Dict[str, str]: Keys are TypeNames, values are versions
    """

    v: Dict[str, str] = {
        "batched.readings": "000",
        "channel.readings": "000",
        "data.channel.gt": "000",
        "fsm.atomic.report": "000",
        "fsm.full.report": "000",
        "gridworks.event.gt.sh.status": "000",
        "gridworks.event.snapshot.spaceheat": "000",
        "gt.sh.booleanactuator.cmd.status": "101",
        "gt.sh.multipurpose.telemetry.status": "100",
        "gt.sh.simple.telemetry.status": "100",
        "gt.sh.status": "110",
        "heartbeat.a": "001",
        "keyparam.change.log": "000",
        "power.watts": "000",
        "snapshot.spaceheat": "000",
        "telemetry.snapshot.spaceheat": "000",
    }

    return v


def status_by_versioned_type_name() -> Dict[str, str]:
    """
    Returns:
        Dict[str, str]: Keys are versioned TypeNames, values are type status
    """

    v: Dict[str, str] = {
        "batched.readings.000": "Active",
        "channel.readings.000": "Pending",
        "data.channel.gt.000": "Active",
        "fsm.atomic.report.000": "Pending",
        "fsm.full.report.000": "Pending",
        "gridworks.event.gt.sh.status.000": "Active",
        "gridworks.event.snapshot.spaceheat.000": "Active",
        "gt.sh.booleanactuator.cmd.status.101": "Pending",
        "gt.sh.multipurpose.telemetry.status.100": "Pending",
        "gt.sh.simple.telemetry.status.100": "Pending",
        "gt.sh.status.110": "Pending",
        "heartbeat.a.001": "Active",
        "keyparam.change.log.000": "Active",
        "power.watts.000": "Active",
        "snapshot.spaceheat.000": "Pending",
        "telemetry.snapshot.spaceheat.000": "Pending",
    }

    return v
