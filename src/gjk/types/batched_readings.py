"""Type batched.readings, version 000"""

import json
import logging
from typing import Any, Dict, List, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from gjk.type_helpers.property_format import (
    LeftRightDotStr,
    UUID4Str,
    check_is_positive_integer,
    check_is_reasonable_unix_time_ms,
    check_is_reasonable_unix_time_s,
)
from gjk.types.channel_readings import ChannelReadings
from gjk.types.data_channel_gt import DataChannelGt
from gjk.types.fsm_atomic_report import FsmAtomicReport
from gjk.types.fsm_full_report import FsmFullReport

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class BatchedReadings(BaseModel):
    """
    Batched Readings.

    A collection of telemetry readings sent up in periodic reports from a SCADA to an AtomicTNode.
    These are organized into data channels (a triple of TelemetryName, AboutNode, and CapturedByNode).
    This replaces GtShStatus. Changes include: FromGNodeId -> FromGNodeInstanveId ReportPeriodS
    -> BatchedTransmissionPeriodS
    """

    from_g_node_alias: LeftRightDotStr
    from_g_node_instance_id: UUID4Str
    about_g_node_alias: LeftRightDotStr
    slot_start_unix_s: int
    batched_transmission_period_s: int
    message_created_ms: int
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
        populate_by_name=True,
    )

    @field_validator("slot_start_unix_s")
    @classmethod
    def _check_slot_start_unix_s(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_s(v)
        except ValueError as e:
            raise ValueError(
                f"SlotStartUnixS failed ReasonableUnixTimeS format validation: {e}",
            ) from e
        return v

    @field_validator("batched_transmission_period_s")
    @classmethod
    def _check_batched_transmission_period_s(cls, v: int) -> int:
        try:
            check_is_positive_integer(v)
        except ValueError as e:
            raise ValueError(
                f"BatchedTransmissionPeriodS failed PositiveInteger format validation: {e}",
            ) from e
        return v

    @field_validator("message_created_ms")
    @classmethod
    def _check_message_created_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"MessageCreatedMs failed ReasonableUnixTimeMs format validation: {e}",
            ) from e
        return v

    @field_validator("fsm_action_list")
    @classmethod
    def check_fsm_action_list(cls, v: List[FsmAtomicReport]) -> List[FsmAtomicReport]:
        """
        Axiom 1: Each of the fsm.atomic.reports in this list must be actions (i.e. IsAction = true).
        """
        for elt in v:
            if not elt.action:
                raise ValueError(
                    "Violates Axiom 1: Each elt of FsmActionList must have an action"
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
                f"Axiom 2 violated. ChannelIds not unique in DataChannelList: <{self}>"
            )
        if len(set(reading_list_ids)) != len(reading_list_ids):
            raise ValueError(
                f"Axiom 2 violated. ChannelIds not unique in ChannelReadingList:\n <{self}>"
            )
        if set(channel_list_ids) != set(reading_list_ids):
            raise ValueError(
                "Axiom 2 violated: must be a bijection between DataChannelList "
                f"and ChannelReadingList:\n <{self}>"
            )
        return self

    @model_validator(mode="after")
    def check_axiom_3(self) -> Self:
        """
        Axiom 3: Time Consistency.
        For every ScadaReadTimeUnixMs   let read_s = read_ms / 1000.  Let start_s be SlotStartUnixS.  Then read_s >= start_s and start_s + BatchedTransmissionPeriodS + 1 + start_s > read_s.
        """
        # Implement check for axiom 3"
        return self

    @classmethod
    def from_dict(cls, d: dict) -> "BatchedReadings":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
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

    def __hash__(self) -> int:
        # Can use as keys in dicts
        return hash(type(self), *tuple(self.__dict__.values()))
