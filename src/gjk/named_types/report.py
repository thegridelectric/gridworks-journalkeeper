"""Type report, version 002"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import PositiveInt, field_validator

from gjk.named_types.channel_readings import ChannelReadings
from gjk.named_types.fsm_full_report import FsmFullReport
from gjk.named_types.machine_states import MachineStates
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UTCSeconds,
    UUID4Str,
)


class Report(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    about_g_node_alias: LeftRightDot
    slot_start_unix_s: UTCSeconds
    slot_duration_s: PositiveInt
    channel_reading_list: List[ChannelReadings]
    state_list: List[MachineStates]
    fsm_report_list: List[FsmFullReport]
    message_created_ms: UTCMilliseconds
    id: UUID4Str
    type_name: Literal["report"] = "report"
    version: Literal["002"] = "002"

    @field_validator("channel_reading_list")
    @classmethod
    def _check_channel_reading_list(
        cls, v: List[ChannelReadings]
    ) -> List[ChannelReadings]:
        return v
