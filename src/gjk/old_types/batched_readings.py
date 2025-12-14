"""Type batched.readings, version 000"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import (
    PositiveInt,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from gjk.named_types.data_channel_gt import DataChannelGt
from gjk.named_types.fsm_atomic_report import FsmAtomicReport
from gjk.named_types.fsm_full_report import FsmFullReport
from gjk.old_types.channel_readings_000 import ChannelReadings000
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UTCSeconds,
    UUID4Str,
)


class BatchedReadings(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    about_g_node_alias: LeftRightDot
    slot_start_unix_s: UTCSeconds
    batched_transmission_period_s: PositiveInt
    message_created_ms: UTCMilliseconds
    data_channel_list: List[DataChannelGt]
    channel_reading_list: List[ChannelReadings000]
    fsm_action_list: List[FsmAtomicReport]
    fsm_report_list: List[FsmFullReport]
    id: UUID4Str
    type_name: Literal["batched.readings"] = "batched.readings"
    version: Literal["000"] = "000"

    @field_validator("fsm_action_list")
    @classmethod
    def check_fsm_action_list(cls, v: List[FsmAtomicReport]) -> List[FsmAtomicReport]:
        """
        Axiom 1: Each of the fsm.atomic.reports in this list must be actions (i.e.ActionType not None).
        """
        for elt in v:
            if elt.action_type is None:
                raise ValueError(
                    "Violates Axiom 1: Each elt of FsmActionList must have an action_type"
                )
        return v

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: DataChannel Consistency.
        There is a bijection between the DataChannelLists and ChannelReadingLists via the ChannelId.
        """
        channel_list_ids = list(map(lambda x: x.id, self.data_channel_list))
        reading_list_ids = list(map(lambda x: x.channel_id, self.channel_reading_list))
        if len(set(channel_list_ids)) != len(channel_list_ids):
            raise ValueError(
                f"Axiom 2 violated. ChannelIds not unique in DataChannelList:\n <{self.to_dict()}>"
            )
        if len(set(reading_list_ids)) != len(reading_list_ids):
            raise ValueError(
                f"Axiom 2 violated. ChannelIds not unique in ChannelReadingList:\n <{self.to_dict()}>"
            )
        if set(channel_list_ids) != set(reading_list_ids):
            raise ValueError(
                "Axiom 2 violated: must be a bijection between DataChannelList "
                f"and ChannelReadingList:\n <{self.model_dump()}>"
            )
        return self

    @model_validator(mode="after")
    def check_axiom_3(self) -> Self:
        """
        Axiom 3: Time Consistency.
        For every ScadaReadTimeUnixMs   let read_s = read_ms / 1000.  Let start_s be SlotStartUnixS.
        Then read_s >= start_s and start_s + BatchedTransmissionPeriodS + 1 + start_s > read_s.
        """
        # delta_s = self.batched_transmission_period_s
        # read_ms_list = list(
        #     chain(
        #         *list(
        #             map(
        #                 lambda x: x.scada_read_time_unix_ms_list,
        #                 self.channel_reading_list,
        #             )
        #         )
        #     )
        # )
        # read_s_set = set(map(lambda x: x / 1000, read_ms_list))
        # for read_s in read_s_set:
        #     if read_s < self.slot_start_unix_s:
        #         raise ValueError(
        #             f"A ScadaReadTime <{read_s}> came before SlotStartUnixS <{self.slot_start_unix_s}>"
        #         )
        #     if read_s > self.slot_start_unix_s + delta_s + 1:
        #         raise ValueError(
        #             f"A ScadaReadTime {read_s} came AFTER SlotStartUnixS  plus "
        #             f"BatchedTransmissionPeriodS <{self.slot_start_unix_s + delta_s}>"
        #        )
        return self
