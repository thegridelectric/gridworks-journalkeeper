"""Type batched.readings, version 000"""

import json
from typing import Any, Dict, List, Literal

from gw.errors import GwTypeError
from gw.utils import recursively_pascal, snake_to_pascal
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from gjk.property_format import (
    LeftRightDot,
    PositiveInteger,
    ReasonableUnixMs,
    ReasonableUnixS,
    UUID4Str,
)
from gjk.types.channel_readings import ChannelReadings
from gjk.types.data_channel_gt import DataChannelGt
from gjk.types.fsm_atomic_report import FsmAtomicReport
from gjk.types.fsm_full_report import FsmFullReport


class BatchedReadings(BaseModel):
    """
    Batched Readings.

    A collection of telemetry readings sent up in periodic reports from a SCADA to an AtomicTNode.
    These are organized into data channels (a triple of TelemetryName, AboutNode, and CapturedByNode).
    This replaces GtShStatus. Changes include: FromGNodeId -> FromGNodeInstanveId ReportPeriodS
    -> BatchedTransmissionPeriodS
    """

    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    about_g_node_alias: LeftRightDot
    slot_start_unix_s: ReasonableUnixS
    batched_transmission_period_s: PositiveInteger
    message_created_ms: ReasonableUnixMs
    data_channel_list: List[DataChannelGt]
    channel_reading_list: List[ChannelReadings]
    fsm_action_list: List[FsmAtomicReport]
    fsm_report_list: List[FsmFullReport]
    id: UUID4Str
    type_name: Literal["batched.readings"] = "batched.readings"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
    )


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
                f"and ChannelReadingList:\n <{self.to_dict()}>"
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

    @classmethod
    def from_dict(cls, d: dict) -> "BatchedReadings":
        if not recursively_pascal(d):
            raise GwTypeError(f"dict is not recursively pascal case! {d}")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "BatchedReadings":
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing must result in dict!\n <{b}>")
        return cls.from_dict(d)

    def to_dict(self) -> Dict[str, Any]:
        """
        Handles lists of enums differently than model_dump
        """
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["DataChannelList"] = [elt.to_dict() for elt in self.data_channel_list]
        d["ChannelReadingList"] = [elt.to_dict() for elt in self.channel_reading_list]
        d["FsmActionList"] = [elt.to_dict() for elt in self.fsm_action_list]
        d["FsmReportList"] = [elt.to_dict() for elt in self.fsm_report_list]
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the batched.readings.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    @classmethod
    def type_name_value(cls) -> str:
        return "batched.readings"
