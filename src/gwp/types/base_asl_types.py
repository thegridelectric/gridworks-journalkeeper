""" List of all the types used by the actor."""

from typing import Dict
from typing import List
from typing import no_type_check

from gwp.types import BatchedReadings_Maker
from gwp.types import ChannelReadings_Maker
from gwp.types import DataChannelGt_Maker
from gwp.types import FsmAtomicReport_Maker
from gwp.types import FsmFullReport_Maker
from gwp.types import GridworksEventGtShStatus_Maker
from gwp.types import GridworksEventSnapshotSpaceheat_Maker
from gwp.types import GtShBooleanactuatorCmdStatus_Maker
from gwp.types import GtShMultipurposeTelemetryStatus_Maker
from gwp.types import GtShSimpleTelemetryStatus_Maker
from gwp.types import GtShStatus_Maker
from gwp.types import HeartbeatA_Maker
from gwp.types import SnapshotSpaceheat_Maker
from gwp.types import TelemetrySnapshotSpaceheat_Maker


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
        "data.channel.gt.000": "Active",
        "fsm.atomic.report.000": "Active",
        "fsm.full.report.000": "Active",
        "gridworks.event.gt.sh.status.000": "Pending",
        "gridworks.event.snapshot.spaceheat.000": "Pending",
        "gt.sh.booleanactuator.cmd.status.101": "Active",
        "gt.sh.multipurpose.telemetry.status.100": "Active",
        "gt.sh.simple.telemetry.status.100": "Active",
        "gt.sh.status.110": "Active",
        "heartbeat.a.001": "Active",
        "snapshot.spaceheat.000": "Active",
        "telemetry.snapshot.spaceheat.000": "Active",
    }

    return v
