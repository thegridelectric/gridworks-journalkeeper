"""Type fsm.atomic.report, version 000"""

import json
import logging
import os
from typing import Any, Dict, Literal, Optional

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from gjk.enums import FsmActionType, FsmEventType, FsmName, FsmReportType

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class FsmAtomicReport(BaseModel):
    """
    Reports of single Fsm Actions and Transitions. The actions is any side-effect, which is
    the way the StateMachine is supposed to cause things happen to the outside world (This could
    include, for example, actuating a relay.) Transitions are intended to be captured by changing
    the handle of the Spaceheat Node whose actor maintains that finite state machine.

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/finite-state-machines.html)
    """

    from_handle: str = Field(
        title="From Handle",
        description=(
            "The Name (as opposed to the handle) of the Spaceheat Node actor issuing the Finite "
            "State Machine report. The actor is meant to realize and be the authority on the "
            "FSM in question. Its handle reflects the state it is in."
        ),
    )
    about_fsm: FsmName = Field(
        title="About Fsm",
        description="The finite state machine this message is about.",
    )
    report_type: FsmReportType = Field(
        title="Report Type",
        description=(
            "Is this reporting an event, an action, or some other thing related to a finite state "
            "machine?"
        ),
    )
    action_type: Optional[FsmActionType] = Field(
        title="Action Type",
        description="The FiniteState Machine Action taken",
        default=None,
    )
    action: Optional[int] = Field(
        title="Action",
        description=(
            "Will typically be a number, usually an integer. For example, if ActionType is RelayPinSet, "
            "then RelayPinSet.DeEnergized = 0 and RelayPinSet.Energized = 1."
        ),
        default=None,
    )
    event_type: Optional[FsmEventType] = Field(
        title="Event Type",
        default=None,
    )
    event: Optional[str] = Field(
        title="Event",
        default=None,
    )
    from_state: Optional[str] = Field(
        title="From State",
        description="The state of the FSM prior to triggering event.",
        default=None,
    )
    to_state: Optional[str] = Field(
        title="To State",
        description="The state of the FSM after the triggering event.",
        default=None,
    )
    unix_time_ms: int = Field(
        title="Unix Time in Milliseconds",
    )
    trigger_id: str = Field(
        title="TriggerId",
        description=(
            "Reference uuid for the triggering event that started a cascade of transitions, events "
            "and side-effect actions - of which this report is one."
        ),
    )
    type_name: Literal["fsm.atomic.report"] = "fsm.atomic.report"
    version: Literal["000"] = "000"

    class Config:
        extra = "allow"
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("from_handle")
    @classmethod
    def _check_from_handle(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(
                f"FromHandle failed SpaceheatName format validation: {e}"
            ) from e
        return v

    @field_validator("unix_time_ms")
    @classmethod
    def _check_unix_time_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"UnixTimeMs failed ReasonableUnixTimeMs format validation: {e}",
            ) from e
        return v

    @field_validator("trigger_id")
    @classmethod
    def _check_trigger_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"TriggerId failed UuidCanonicalTextual format validation: {e}",
            ) from e
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Action and ActionType exist iff  ReportType is Action.
        The Optional Attributes ActionType and Action exist if and only if IsAction is true.
        """
        # TODO: Implement check for axiom 1"
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: If Action exists, then it belongs to the un-versioned enum selected in the ActionType.

        """
        # TODO: Implement check for axiom 2"
        return self

    @model_validator(mode="after")
    def check_axiom_3(self) -> Self:
        """
        Axiom 3: EventType, Event, FromState, ToState exist iff ReportType is Event.

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
        d["AboutFsm"] = d["AboutFsm"].value
        d["ReportType"] = d["ReportType"].value
        if "ActionType" in d.keys():
            d["ActionType"] = d["ActionType"].value
        if "EventType" in d.keys():
            d["EventType"] = d["EventType"].value
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
        del d["AboutFsm"]
        d["AboutFsmGtEnumSymbol"] = FsmName.value_to_symbol(self.about_fsm)
        del d["ReportType"]
        d["ReportTypeGtEnumSymbol"] = FsmReportType.value_to_symbol(self.report_type)
        if "ActionType" in d.keys():
            del d["ActionType"]
            d["ActionTypeGtEnumSymbol"] = FsmActionType.value_to_symbol(
                self.action_type
            )
        if "EventType" in d.keys():
            del d["EventType"]
            d["EventTypeGtEnumSymbol"] = FsmEventType.value_to_symbol(self.event_type)
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the fsm.atomic.report.000 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class FsmAtomicReportMaker:
    type_name = "fsm.atomic.report"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: FsmAtomicReport) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> FsmAtomicReport:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a fsm.atomic.report.000 type

        Returns:
            FsmAtomicReport instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> FsmAtomicReport:
        """
        Translates a dict representation of a fsm.atomic.report.000 message object
        into the Python class object.
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "FromHandle" not in d2.keys():
            raise GwTypeError(f"dict missing FromHandle: <{d2}>")
        if "AboutFsmGtEnumSymbol" in d2.keys():
            value = FsmName.symbol_to_value(d2["AboutFsmGtEnumSymbol"])
            d2["AboutFsm"] = FsmName(value)
            del d2["AboutFsmGtEnumSymbol"]
        elif "AboutFsm" in d2.keys():
            if d2["AboutFsm"] not in FsmName.values():
                d2["AboutFsm"] = FsmName.default()
            else:
                d2["AboutFsm"] = FsmName(d2["AboutFsm"])
        else:
            raise GwTypeError(
                f"both AboutFsmGtEnumSymbol and AboutFsm missing from dict <{d2}>",
            )
        if "ReportTypeGtEnumSymbol" in d2.keys():
            value = FsmReportType.symbol_to_value(d2["ReportTypeGtEnumSymbol"])
            d2["ReportType"] = FsmReportType(value)
            del d2["ReportTypeGtEnumSymbol"]
        elif "ReportType" in d2.keys():
            if d2["ReportType"] not in FsmReportType.values():
                d2["ReportType"] = FsmReportType.default()
            else:
                d2["ReportType"] = FsmReportType(d2["ReportType"])
        else:
            raise GwTypeError(
                f"both ReportTypeGtEnumSymbol and ReportType missing from dict <{d2}>",
            )
        if "ActionType" in d2.keys():
            if d2["ActionType"] not in FsmActionType.values():
                d2["ActionType"] = FsmActionType.default()
            else:
                d2["ActionType"] = FsmActionType(d2["ActionType"])
        if "ActionTypeGtEnumSymbol" in d2.keys():
            value = FsmActionType.symbol_to_value(d2["ActionTypeGtEnumSymbol"])
            d2["ActionType"] = FsmActionType(value)
            del d2["ActionTypeGtEnumSymbol"]
        if "EventType" in d2.keys():
            if d2["EventType"] not in FsmEventType.values():
                d2["EventType"] = FsmEventType.default()
            else:
                d2["EventType"] = FsmEventType(d2["EventType"])
        if "EventTypeGtEnumSymbol" in d2.keys():
            value = FsmEventType.symbol_to_value(d2["EventTypeGtEnumSymbol"])
            d2["EventType"] = FsmEventType(value)
            del d2["EventTypeGtEnumSymbol"]
        if "UnixTimeMs" not in d2.keys():
            raise GwTypeError(f"dict missing UnixTimeMs: <{d2}>")
        if "TriggerId" not in d2.keys():
            raise GwTypeError(f"dict missing TriggerId: <{d2}>")
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret fsm.atomic.report version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return FsmAtomicReport(**d3)


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


def check_is_spaceheat_name(v: str) -> None:
    """Check SpaceheatName Format.

    Validates if the provided string adheres to the SpaceheatName format:
    Lowercase alphanumeric words separated by hypens

    Args:
        candidate (str): The string to be validated.

    Raises:
        ValueError: If the provided string is not in SpaceheatName format.
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
        for char in word:
            if not (char.isalnum() or char == "-"):
                raise ValueError(
                    f"words of <{v}> split by by '.' must be alphanumeric or hyphen."
                )
    if not v.islower():
        raise ValueError(f"<{v}> must be lowercase.")


def check_is_uuid_canonical_textual(v: str) -> None:
    """Checks UuidCanonicalTextual format

    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not UuidCanonicalTextual format
    """
    try:
        x = v.split("-")
    except AttributeError as e:
        raise ValueError(f"Failed to split on -: {e}") from e
    if len(x) != 5:
        raise ValueError(f"<{v}> split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError as e:
            raise ValueError(f"Words of <{v}> are not all hex") from e
    if len(x[0]) != 8:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[1]) != 4:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[2]) != 4:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[3]) != 4:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[4]) != 12:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
