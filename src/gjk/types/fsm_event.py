"""Type fsm.event, version 000"""

import json
import logging
import os
from typing import Any, Dict, Literal

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from gjk.enums import (
    ChangeAquastatControl,
    ChangeHeatcallSource,
    ChangeHeatPumpControl,
    ChangeLgOperatingMode,
    ChangePrimaryPumpState,
    ChangeRelayPin,
    ChangeRelayState,
    ChangeStoreFlowDirection,
    ChangeValveState,
    FsmEventType,
    ChangePrimaryPumpControl,
)

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class FsmEvent(BaseModel):
    """
    Finite State Machine Event Command.

    A message sent to a SpaceheatNode wher ethe Node implements a finite state machine. The
    message is intended to be an FSM Events (aka Trigger) that allow a state machine to react
    (by starting a Transition and any side-effect Actions).

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/finite-state-machines.html)
    """

    from_handle: str = Field(
        title="From Handle",
    )
    to_handle: str = Field(
        title="To Handle",
    )
    event_type: FsmEventType = Field(
        title="Event Type",
        description=(
            "Typically the set of events allowed will be determined implicitly by the ToHandle. "
            "This is clarified in the message; and if the message does not clarify the appropriate "
            "understanding of the finite state machine and its events then the message will likely "
            "be ignored."
        ),
    )
    event_name: str = Field(
        title="Event Name",
        description=(
            "This should be the name that the receiving Spaceheat Node's finite state machine "
            "uses for an event that triggers a transition."
        ),
    )
    trigger_id: str = Field(
        title="Trigger Id",
        description=(
            "Reference uuid for the triggering event that started a cascade of transitions, events "
            "and side-effect actions - of which this event is one."
        ),
    )
    send_time_unix_ms: int = Field(
        title="Sent Time Unix Ms",
    )
    type_name: Literal["fsm.event"] = "fsm.event"
    version: Literal["000"] = "000"

    class Config:
        extra = "allow"
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("from_handle")
    @classmethod
    def _check_from_handle(cls, v: str) -> str:
        try:
            check_is_handle_name(v)
        except ValueError as e:
            raise ValueError(
                f"FromHandle failed HandleName format validation: {e}"
            ) from e
        return v

    @field_validator("to_handle")
    @classmethod
    def _check_to_handle(cls, v: str) -> str:
        try:
            check_is_handle_name(v)
        except ValueError as e:
            raise ValueError(
                f"ToHandle failed HandleNameName format validation: {e}"
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

    @field_validator("send_time_unix_ms")
    @classmethod
    def _check_send_time_unix_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"SendTimeUnixMs failed ReasonableUnixTimeMs format validation: {e}",
            ) from e
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom : EventName must belong to the enum selected in the EventType.

        """
        if (
            self.event_type == FsmEventType.ChangeRelayPin
            and self.event_name not in ChangeRelayPin.values()
        ) or (
            self.event_type == FsmEventType.ChangeRelayState
            and self.event_name not in ChangeRelayState.values()
        ):
            raise ValueError(
                f"EventName {self.event_name} must belong to {self.event_type} values!"
            )

        if (
            self.event_type == FsmEventType.ChangeValveState
            and self.event_name not in ChangeValveState.values()
        ) or (
            self.event_type == FsmEventType.ChangeStoreFlowDirection
            and self.event_name not in ChangeStoreFlowDirection.values()
        ):
            raise ValueError(
                f"EventName {self.event_name} must belong to {self.event_type} values!"
            )
        if (
            self.event_type == FsmEventType.ChangeHeatcallSource
            and self.event_name not in ChangeHeatcallSource.values()
        ) or (
            self.event_type == FsmEventType.ChangeAquastatControl
            and self.event_name not in ChangeAquastatControl.values()
        ):
            raise ValueError(
                f"EventName {self.event_name} must belong to {self.event_type} values!"
            )
        if (
            self.event_type == FsmEventType.ChangeHeatPumpControl
            and self.event_name not in ChangeHeatPumpControl.values()
        ) or (
            self.event_type == FsmEventType.ChangeLgOperatingMode
            and self.event_name not in ChangeLgOperatingMode.values()
        ):
            raise ValueError(
                f"EventName {self.event_name} must belong to {self.event_type} values!"
            )
        if (
            self.event_type == FsmEventType.ChangePrimaryPumpState
            and self.event_name not in ChangePrimaryPumpState.values()
        ) or (
            self.event_type == FsmEventType.ChangePrimaryPumpControl
            and self.event_name not in ChangePrimaryPumpControl.values()
        ):
            raise ValueError(
                f"EventName {self.event_name} must belong to {self.event_type} values!"
            )

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
        del d["EventType"]
        d["EventTypeGtEnumSymbol"] = FsmEventType.value_to_symbol(self.event_type)
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the fsm.event.000 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class FsmEventMaker:
    type_name = "fsm.event"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: FsmEvent) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> FsmEvent:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a fsm.event.000 type

        Returns:
            FsmEvent instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> FsmEvent:
        """
        Translates a dict representation of a fsm.event.000 message object
        into the Python class object.
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "FromHandle" not in d2.keys():
            raise GwTypeError(f"dict missing FromHandle: <{d2}>")
        if "ToHandle" not in d2.keys():
            raise GwTypeError(f"dict missing ToHandle: <{d2}>")
        if "EventTypeGtEnumSymbol" in d2.keys():
            value = FsmEventType.symbol_to_value(d2["EventTypeGtEnumSymbol"])
            d2["EventType"] = FsmEventType(value)
            del d2["EventTypeGtEnumSymbol"]
        elif "EventType" in d2.keys():
            if d2["EventType"] not in FsmEventType.values():
                d2["EventType"] = FsmEventType.default()
            else:
                d2["EventType"] = FsmEventType(d2["EventType"])
        else:
            raise GwTypeError(
                f"both EventTypeGtEnumSymbol and EventType missing from dict <{d2}>",
            )
        if "EventName" not in d2.keys():
            raise GwTypeError(f"dict missing EventName: <{d2}>")
        if "TriggerId" not in d2.keys():
            raise GwTypeError(f"dict missing TriggerId: <{d2}>")
        if "SendTimeUnixMs" not in d2.keys():
            raise GwTypeError(f"dict missing SendTimeUnixMs: <{d2}>")
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret fsm.event version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return FsmEvent(**d3)


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


def check_is_handle_name(v: str) -> None:
    """Check HandleName Format.

    Validates if the provided string adheres to the HandleName format:
    words separated by periods, where the worlds are lowercase alphanumeric plus hyphens

    Args:
        candidate (str): The string to be validated.

    Raises:
        ValueError: If the provided string is not in HandleName format.
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
