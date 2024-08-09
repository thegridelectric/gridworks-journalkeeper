"""List of all the types used by the actor."""

from typing import Dict, List, no_type_check

from gjk.gs import DispatchMaker, PowerMaker
from gjk.types.batched_readings import BatchedReadingsMaker
from gjk.types.channel_readings import ChannelReadingsMaker
from gjk.types.data_channel_gt import DataChannelGtMaker
from gjk.types.fsm_atomic_report import FsmAtomicReportMaker
from gjk.types.fsm_full_report import FsmFullReportMaker
from gjk.types.gridworks_event_gt_sh_status import GridworksEventGtShStatusMaker
from gjk.types.gridworks_event_snapshot_spaceheat import (
    GridworksEventSnapshotSpaceheatMaker,
)
from gjk.types.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatusMaker
from gjk.types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatusMaker,
)
from gjk.types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatusMaker
from gjk.types.gt_sh_status import GtShStatusMaker
from gjk.types.heartbeat_a import HeartbeatAMaker
from gjk.types.keyparam_change_log import KeyparamChangeLogMaker
from gjk.types.power_watts import PowerWattsMaker
from gjk.types.snapshot_spaceheat import SnapshotSpaceheatMaker
from gjk.types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheatMaker

TypeMakerByName: Dict[str, PowerMaker] = {}


@no_type_check
def type_makers() -> List[PowerMaker]:
    return [
        DispatchMaker,  # special non-json serialization
        PowerMaker,  # special non-json serialization
        BatchedReadingsMaker,
        ChannelReadingsMaker,
        DataChannelGtMaker,
        FsmAtomicReportMaker,
        FsmFullReportMaker,
        GridworksEventGtShStatusMaker,
        GridworksEventSnapshotSpaceheatMaker,
        GtShBooleanactuatorCmdStatusMaker,
        GtShMultipurposeTelemetryStatusMaker,
        GtShSimpleTelemetryStatusMaker,
        GtShStatusMaker,
        HeartbeatAMaker,
        KeyparamChangeLogMaker,
        PowerWattsMaker,
        SnapshotSpaceheatMaker,
        TelemetrySnapshotSpaceheatMaker,
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
        "data.channel.gt": "001",
        "fsm.atomic.report": "000",
        "fsm.full.report": "000",
        "g.node.gt": "002",
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
        "channel.readings.000": "Active",
        "data.channel.gt.001": "Pending",
        "fsm.atomic.report.000": "Active",
        "fsm.full.report.000": "Active",
        "g.node.gt.002": "Active",
        "gridworks.event.gt.sh.status.000": "Active",
        "gridworks.event.snapshot.spaceheat.000": "Active",
        "gt.sh.booleanactuator.cmd.status.101": "Active",
        "gt.sh.multipurpose.telemetry.status.100": "Active",
        "gt.sh.simple.telemetry.status.100": "Active",
        "gt.sh.status.110": "Active",
        "heartbeat.a.001": "Active",
        "keyparam.change.log.000": "Active",
        "power.watts.000": "Active",
        "snapshot.spaceheat.000": "Active",
        "telemetry.snapshot.spaceheat.000": "Active",
    }

    return v
