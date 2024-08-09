"""Type batched.readings, version 000"""

import json
import logging
import os
from typing import Any, Dict, List, Literal

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from gjk.types.channel_readings import ChannelReadings, ChannelReadingsMaker
from gjk.types.data_channel_gt import DataChannelGt, DataChannelGtMaker
from gjk.types.fsm_atomic_report import FsmAtomicReport, FsmAtomicReportMaker
from gjk.types.fsm_full_report import FsmFullReport, FsmFullReportMaker

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

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

    from_g_node_alias: str = Field(
        title="FromGNodeAlias",
    )
    from_g_node_instance_id: str = Field(
        title="FromGNodeInstanceId",
    )
    about_g_node_alias: str = Field(
        title="AboutGNodeAlias",
    )
    slot_start_unix_s: int = Field(
        title="SlotStartUnixS",
    )
    batched_transmission_period_s: int = Field(
        title="BatchedTransmissionPeriodS",
    )
    message_created_ms: int = Field(
        title="MessageCreatedMs",
        description=(
            "The SCADA timestamp for when this message was created. If the message is not acked "
            "by the AtomicTNode, the message is stored and sent again later - so the MessageCreatedMs "
            "may occur significantly before the timestamp for when the message is put into the "
            "persistent store."
        ),
    )
    data_channel_list: List[DataChannelGt] = Field(
        title="DataChannel List",
        description=(
            "The list of data channels for which there is data getting reported in this batched "
            "reading. It is a subset of all the data channels for the SCADA - may not be all "
            "of them."
        ),
    )
    channel_reading_list: List[ChannelReadings] = Field(
        title="ChannelReadingList",
    )
    fsm_action_list: List[FsmAtomicReport] = Field(
        title="Finite State Machine Action List",
        description=(
            "FSM Actions (that is, side-effects of state machine transitions with real-world "
            "changes to the underlying TerminalAsset)."
            "[More info](https://gridworks-protocol.readthedocs.io/en/latest/finite-state-machines.html)"
        ),
    )
    fsm_report_list: List[FsmFullReport] = Field(
        title="Finite State Machine Report List",
        description=(
            "FSM Reports are the cacading events, actions and transitions caused by a single "
            "high-level event. There is duplication with the action list."
            "[More info](https://gridworks-protocol.readthedocs.io/en/latest/finite-state-machines.html)"
        ),
    )
    id: str = Field(
        title="Batched Reading Id",
        description="Globally Unique identifier for a BatchedReadings message",
    )
    type_name: Literal["batched.readings"] = "batched.readings"
    version: Literal["000"] = "000"

    class Config:
        extra = "allow"
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("from_g_node_alias")
    @classmethod
    def _check_from_g_node_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"FromGNodeAlias failed LeftRightDot format validation: {e}",
            ) from e
        return v

    @field_validator("from_g_node_instance_id")
    @classmethod
    def _check_from_g_node_instance_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"FromGNodeInstanceId failed UuidCanonicalTextual format validation: {e}",
            ) from e
        return v

    @field_validator("about_g_node_alias")
    @classmethod
    def _check_about_g_node_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"AboutGNodeAlias failed LeftRightDot format validation: {e}",
            ) from e
        return v

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
        Axiom 1: Each of the fsm.atomic.reports in this list must be actions.
        """
        for elt in v:
            if not elt.action:
                raise ValueError(
                    "Violates Axiom 1: Each elt of FsmActionList must have an action"
                )
        return v

    @field_validator("id")
    @classmethod
    def _check_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"Id failed UuidCanonicalTextual format validation: {e}"
            ) from e
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
        # TODO: Implement check for axiom 3"
        return self

    def as_dict(self) -> Dict[str, Any]:
        """
        Main step in serializing the object. Encodes enums as their 8-digit random hex symbol if
        settings.encode_enums = 1.
        """
        if ENCODE_ENUMS:
            return self.enum_encoded_dict()
        else:
            return self.plain_enum_dict()

    def plain_enum_dict(self) -> Dict[str, Any]:
        """
        Returns enums as their values.
        """
        d = {
            snake_to_pascal(key): value
            for key, value in self.model_dump().items()
            if value is not None
        }
        # Recursively calling as_dict()
        data_channel_list = []
        for elt in self.data_channel_list:
            data_channel_list.append(elt.as_dict())
        d["DataChannelList"] = data_channel_list
        # Recursively calling as_dict()
        channel_reading_list = []
        for elt in self.channel_reading_list:
            channel_reading_list.append(elt.as_dict())
        d["ChannelReadingList"] = channel_reading_list
        # Recursively calling as_dict()
        fsm_action_list = []
        for elt in self.fsm_action_list:
            fsm_action_list.append(elt.as_dict())
        d["FsmActionList"] = fsm_action_list
        # Recursively calling as_dict()
        fsm_report_list = []
        for elt in self.fsm_report_list:
            fsm_report_list.append(elt.as_dict())
        d["FsmReportList"] = fsm_report_list
        return d

    def enum_encoded_dict(self) -> Dict[str, Any]:
        """
        Encodes enums as their 8-digit random hex symbol
        """
        d = {
            snake_to_pascal(key): value
            for key, value in self.model_dump().items()
            if value is not None
        }
        # Recursively calling as_dict()
        data_channel_list = []
        for elt in self.data_channel_list:
            data_channel_list.append(elt.as_dict())
        d["DataChannelList"] = data_channel_list
        # Recursively calling as_dict()
        channel_reading_list = []
        for elt in self.channel_reading_list:
            channel_reading_list.append(elt.as_dict())
        d["ChannelReadingList"] = channel_reading_list
        # Recursively calling as_dict()
        fsm_action_list = []
        for elt in self.fsm_action_list:
            fsm_action_list.append(elt.as_dict())
        d["FsmActionList"] = fsm_action_list
        # Recursively calling as_dict()
        fsm_report_list = []
        for elt in self.fsm_report_list:
            fsm_report_list.append(elt.as_dict())
        d["FsmReportList"] = fsm_report_list
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the batched.readings.000 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class BatchedReadingsMaker:
    type_name = "batched.readings"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: BatchedReadings) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> BatchedReadings:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a batched.readings.000 type

        Returns:
            BatchedReadings instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> BatchedReadings:
        """
        Translates a dict representation of a batched.readings.000 message object
        into the Python class object.
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "FromGNodeAlias" not in d2.keys():
            raise GwTypeError(f"dict missing FromGNodeAlias: <{d2}>")
        if "FromGNodeInstanceId" not in d2.keys():
            raise GwTypeError(f"dict missing FromGNodeInstanceId: <{d2}>")
        if "AboutGNodeAlias" not in d2.keys():
            raise GwTypeError(f"dict missing AboutGNodeAlias: <{d2}>")
        if "SlotStartUnixS" not in d2.keys():
            raise GwTypeError(f"dict missing SlotStartUnixS: <{d2}>")
        if "BatchedTransmissionPeriodS" not in d2.keys():
            raise GwTypeError(f"dict missing BatchedTransmissionPeriodS: <{d2}>")
        if "MessageCreatedMs" not in d2.keys():
            raise GwTypeError(f"dict missing MessageCreatedMs: <{d2}>")
        if "DataChannelList" not in d2.keys():
            raise GwTypeError(f"dict missing DataChannelList: <{d2}>")
        if not isinstance(d2["DataChannelList"], List):
            raise GwTypeError(
                f"DataChannelList <{d2['DataChannelList']}> must be a List!"
            )
        data_channel_list = []
        for elt in d2["DataChannelList"]:
            if not isinstance(elt, dict):
                raise GwTypeError(
                    f"DataChannelList <{d2['DataChannelList']}> must be a List of DataChannelGt types"
                )
            t = DataChannelGtMaker.dict_to_tuple(elt)
            data_channel_list.append(t)
        d2["DataChannelList"] = data_channel_list
        if "ChannelReadingList" not in d2.keys():
            raise GwTypeError(f"dict missing ChannelReadingList: <{d2}>")
        if not isinstance(d2["ChannelReadingList"], List):
            raise GwTypeError(
                f"ChannelReadingList <{d2['ChannelReadingList']}> must be a List!"
            )
        channel_reading_list = []
        for elt in d2["ChannelReadingList"]:
            if not isinstance(elt, dict):
                raise GwTypeError(
                    f"ChannelReadingList <{d2['ChannelReadingList']}> must be a List of ChannelReadings types"
                )
            t = ChannelReadingsMaker.dict_to_tuple(elt)
            channel_reading_list.append(t)
        d2["ChannelReadingList"] = channel_reading_list
        if "FsmActionList" not in d2.keys():
            raise GwTypeError(f"dict missing FsmActionList: <{d2}>")
        if not isinstance(d2["FsmActionList"], List):
            raise GwTypeError(f"FsmActionList <{d2['FsmActionList']}> must be a List!")
        fsm_action_list = []
        for elt in d2["FsmActionList"]:
            if not isinstance(elt, dict):
                raise GwTypeError(
                    f"FsmActionList <{d2['FsmActionList']}> must be a List of FsmAtomicReport types"
                )
            t = FsmAtomicReportMaker.dict_to_tuple(elt)
            fsm_action_list.append(t)
        d2["FsmActionList"] = fsm_action_list
        if "FsmReportList" not in d2.keys():
            raise GwTypeError(f"dict missing FsmReportList: <{d2}>")
        if not isinstance(d2["FsmReportList"], List):
            raise GwTypeError(f"FsmReportList <{d2['FsmReportList']}> must be a List!")
        fsm_report_list = []
        for elt in d2["FsmReportList"]:
            if not isinstance(elt, dict):
                raise GwTypeError(
                    f"FsmReportList <{d2['FsmReportList']}> must be a List of FsmFullReport types"
                )
            t = FsmFullReportMaker.dict_to_tuple(elt)
            fsm_report_list.append(t)
        d2["FsmReportList"] = fsm_report_list
        if "Id" not in d2.keys():
            raise GwTypeError(f"dict missing Id: <{d2}>")
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret batched.readings version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return BatchedReadings(**d3)


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods, with
    the most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
    """
    try:
        x = v.split(".")
    except Exception as e:
        raise ValueError(f"Failed to seperate <{v}> into words with split'.'") from e
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of <{v}> must start with alphabet char."
        )
    for word in x:
        if not word.isalnum():
            raise ValueError(f"words of <{v}> split by by '.' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of <{v}> must be lowercase.")


def check_is_positive_integer(v: int) -> None:
    """
    Must be positive when interpreted as an integer. Interpretation as an
    integer follows the pydantic rules for this - which will round down
    rational numbers. So 1.7 will be interpreted as 1 and is also fine,
    while 0.5 is interpreted as 0 and will raise an exception.

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v < 1
    """
    v2 = int(v)
    if v2 < 1:
        raise ValueError(f"<{v}> is not PositiveInteger")


def check_is_reasonable_unix_time_ms(v: int) -> None:
    """Checks ReasonableUnixTimeMs format

    ReasonableUnixTimeMs format: unix milliseconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeMs format
    """
    from datetime import datetime, timezone

    start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(3000, 1, 1, tzinfo=timezone.utc)

    start_timestamp_ms = int(start_date.timestamp() * 1000)
    end_timestamp_ms = int(end_date.timestamp() * 1000)

    if v < start_timestamp_ms:
        raise ValueError(f"{v} must be after Jan 1 2000")
    if v > end_timestamp_ms:
        raise ValueError(f"{v} must be before Jan 1 3000")


def check_is_reasonable_unix_time_s(v: int) -> None:
    """Checks ReasonableUnixTimeS format

    ReasonableUnixTimeS format: unix seconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeS format
    """
    from datetime import datetime, timezone

    start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(3000, 1, 1, tzinfo=timezone.utc)

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    if v < start_timestamp:
        raise ValueError(f"{v} must be after Jan 1 2000")
    if v > end_timestamp:
        raise ValueError(f"{v} must be before Jan 1 3000")


def check_is_uuid_canonical_textual(v: str) -> None:
    """Checks UuidCanonicalTextual format

    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not UuidCanonicalTextual format
    """
    phi_fun_check_it_out = 5
    two_cubed_too_cute = 8
    bachets_fun_four = 4
    the_sublime_twelve = 12
    try:
        x = v.split("-")
    except AttributeError as e:
        raise ValueError(f"Failed to split on -: {e}") from e
    if len(x) != phi_fun_check_it_out:
        raise ValueError(f"<{v}> split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError as e:
            raise ValueError(f"Words of <{v}> are not all hex") from e
    if len(x[0]) != two_cubed_too_cute:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[1]) != bachets_fun_four:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[2]) != bachets_fun_four:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[3]) != bachets_fun_four:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[4]) != the_sublime_twelve:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
