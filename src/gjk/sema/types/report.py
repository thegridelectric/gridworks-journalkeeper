from typing import Literal
from gjk.sema.base import SemaType
from gjk.sema.property_format import LeftRightDot
from gjk.sema.property_format import PositiveInt
from gjk.sema.property_format import UTCMilliseconds
from gjk.sema.property_format import UTCSeconds
from gjk.sema.property_format import UUID4Str
from gjk.sema.types.channel_readings import ChannelReadings
from gjk.sema.types.fsm_full_report import FsmFullReport
from gjk.sema.types.machine_states import MachineStates


class Report(SemaType):
    """Sema: https://schemas.electricity.works/types/report/003"""

    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    about_g_node_alias: LeftRightDot
    slot_start_unix_s: UTCSeconds
    slot_duration_s: PositiveInt
    channel_reading_list: list[ChannelReadings]
    state_list: list[MachineStates]
    fsm_report_list: list[FsmFullReport]
    message_created_ms: UTCMilliseconds
    id: UUID4Str
    type_name: Literal["report"] = "report"
    version: Literal["003"] = "003"
