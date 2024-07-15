"""Type fsm.atomic.report, version 000"""

import json
import logging
from typing import Any
from typing import Dict
from typing import Literal
from typing import Optional

from gw.errors import GwTypeError
from gw.utils import is_pascal_case
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic.alias_generators import to_pascal
from pydantic.alias_generators import to_snake

from gwp.enums import FsmActionType
from gwp.enums import FsmEventType
from gwp.enums import FsmName
from gwp.enums import FsmReportType


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
        alias_generator = to_pascal

    @field_validator("from_handle")
    def _check_from_handle(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(f"FromHandle failed SpaceheatName format validation: {e}")
        return v

    @field_validator("unix_time_ms")
    def _check_unix_time_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"UnixTimeMs failed ReasonableUnixTimeMs format validation: {e}"
            )
        return v

    @field_validator("trigger_id")
    def _check_trigger_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"TriggerId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @model_validator
    def check_axiom_1(cls, v: dict) -> dict:
        """
        Axiom 1: Action and ActionType exist iff  ReportType is Action.
        The Optional Attributes ActionType and Action exist if and only if IsAction is true.
        """
        # TODO: Implement check for axiom 1"
        return v

    @model_validator
    def check_axiom_2(cls, v: dict) -> dict:
        """
        Axiom 2: If Action exists, then it belongs to the un-versioned enum selected in the ActionType.

        """
        # TODO: Implement check for axiom 2"
        return v

    @model_validator
    def check_axiom_3(cls, v: dict) -> dict:
        """
        Axiom 3: EventType, Event, FromState, ToState exist iff ReportType is Event.

        """
        # TODO: Implement check for axiom 3"
        return v

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        fsm.atomic.report.000 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        fsm.atomic.report.000 type. Unlike the standard python dict method,
        it makes the following substantive changes:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.
        """
        d = {
            to_pascal(key): value
            for key, value in self.model_dump().items()
            if value is not None
        }
        del d["AboutFsm"]
        d["AboutFsmGtEnumSymbol"] = FsmName.value_to_symbol(self.about_fsm)
        del d["ReportType"]
        d["ReportTypeGtEnumSymbol"] = FsmReportType.value_to_symbol(self.report_type)
        if "ActionType" in d.keys():
            del d["ActionType"]
            d["ActionTypeGtEnumSymbol"] = FsmActionType.value_to_symbol(self.ActionType)
        if "EventType" in d.keys():
            del d["EventType"]
            d["EventTypeGtEnumSymbol"] = FsmEventType.value_to_symbol(self.EventType)
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the fsm.atomic.report.000 representation.

        Instances in the class are python-native representations of fsm.atomic.report.000
        objects, while the actual fsm.atomic.report.000 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is FsmAtomicReport.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class FsmAtomicReport_Maker:
    type_name = "fsm.atomic.report"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: FsmAtomicReport) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> FsmAtomicReport:
        """
        Given a serialized JSON type object, returns the Python class object.
        """
        try:
            d = json.loads(t)
        except TypeError:
            raise GwTypeError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing <{t}> must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> FsmAtomicReport:
        """
        Deserialize a dictionary representation of a fsm.atomic.report.000 message object
        into a FsmAtomicReport python object for internal use.

        This is the near-inverse of the FsmAtomicReport.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a GwTypeError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           GwTypeError: if the dict cannot be turned into a FsmAtomicReport object.

        Returns:
            FsmAtomicReport
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "FromHandle" not in d2.keys():
            raise GwTypeError(f"dict missing FromHandle: <{d2}>")
        if "AboutFsmGtEnumSymbol" not in d2.keys():
            raise GwTypeError(f"AboutFsmGtEnumSymbol missing from dict <{d2}>")
        value = FsmName.symbol_to_value(d2["AboutFsmGtEnumSymbol"])
        d2["AboutFsm"] = FsmName(value)
        del d2["AboutFsmGtEnumSymbol"]
        if "ReportTypeGtEnumSymbol" not in d2.keys():
            raise GwTypeError(f"ReportTypeGtEnumSymbol missing from dict <{d2}>")
        value = FsmReportType.symbol_to_value(d2["ReportTypeGtEnumSymbol"])
        d2["ReportType"] = FsmReportType(value)
        del d2["ReportTypeGtEnumSymbol"]
        if "ActionTypeGtEnumSymbol" in d2.keys():
            value = FsmActionType.symbol_to_value(d2["ActionTypeGtEnumSymbol"])
            d2["ActionType"] = FsmActionType(value)
            del d2["ActionTypeGtEnumSymbol"]
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
        d3 = {to_snake(key): value for key, value in d2.items()}
        return FsmAtomicReport(**d3)


def check_is_reasonable_unix_time_ms(v: int) -> None:
    """Checks ReasonableUnixTimeMs format

    ReasonableUnixTimeMs format: unix milliseconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeMs format
    """
    from datetime import datetime
    from datetime import timezone

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
    Lowercase words separated by periods, where word characters can be alphanumeric
    or a hyphen, and the first word starts with an alphabet character.

    Args:
        candidate (str): The string to be validated.

    Raises:
        ValueError: If the provided string is not in SpaceheatName format.
    """
    from typing import List

    try:
        x: List[str] = v.split(".")
    except:
        raise ValueError(f"Failed to seperate <{v}> into words with split'.'")
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
        raise ValueError(f"Failed to split on -: {e}")
    if len(x) != 5:
        raise ValueError(f"<{v}> split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError:
            raise ValueError(f"Words of <{v}> are not all hex")
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
