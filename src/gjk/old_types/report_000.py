"""Type report, version 000"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import (
    PositiveInt,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from gjk.named_types.fsm_atomic_report import FsmAtomicReport
from gjk.named_types.fsm_full_report import FsmFullReport
from gjk.old_types.channel_readings_001 import ChannelReadings001
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UTCSeconds,
    UUID4Str,
)


class Report000(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    about_g_node_alias: LeftRightDot
    slot_start_unix_s: UTCSeconds
    batched_transmission_period_s: PositiveInt
    channel_reading_list: List[ChannelReadings001]
    fsm_action_list: List[FsmAtomicReport]
    fsm_report_list: List[FsmFullReport]
    message_created_ms: UTCMilliseconds
    id: UUID4Str
    type_name: Literal["report"] = "report"
    version: Literal["000"] = "000"

    @field_validator("channel_reading_list")
    @classmethod
    def check_channel_reading_list(
        cls, v: List[ChannelReadings001]
    ) -> List[ChannelReadings001]:
        """
        Axiom 2: Unique Channel names and Ids.
        The ChannelIds in the ChannelReadingList are all unique, as are the ChannelNames.
        """
        # Implement Axiom(s)
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Time Consistency.
        For every ScadaReadTimeUnixMs   let read_s = read_ms / 1000.  Let start_s be SlotStartUnixS.  Then read_s >= start_s and start_s + BatchedTransmissionPeriodS + 1 + start_s > read_s.
        """
        # Implement check for axiom 1"
        return self
