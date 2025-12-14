"""Type gt.sh.status, version 110"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import StrictInt

from gjk.old_types.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatus
from gjk.old_types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from gjk.old_types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus
from gjk.property_format import (
    LeftRightDot,
    UTCSeconds,
    UUID4Str,
)


class GtShStatus(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_id: UUID4Str
    about_g_node_alias: LeftRightDot
    slot_start_unix_s: UTCSeconds
    reporting_period_s: StrictInt
    simple_telemetry_list: List[GtShSimpleTelemetryStatus]
    multipurpose_telemetry_list: List[GtShMultipurposeTelemetryStatus]
    booleanactuator_cmd_list: List[GtShBooleanactuatorCmdStatus]
    status_uid: UUID4Str
    type_name: Literal["gt.sh.status"] = "gt.sh.status"
    version: Literal["110"] = "110"
