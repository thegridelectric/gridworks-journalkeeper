"""Type fsm.event, version 000"""

import json
import logging
from typing import Any, Dict, Literal

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

from gjk.enums import FsmEventType
from gjk.type_helpers.property_format import (
    ReasonableUnixMs,
    UUID4Str,
    check_is_handle_name,
)

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

    from_handle: str
    to_handle: str
    event_type: FsmEventType
    event_name: str
    trigger_id: UUID4Str
    send_time_unix_ms: ReasonableUnixMs
    type_name: Literal["fsm.event"] = "fsm.event"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
    )

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
                f"ToHandle failed HandleName format validation: {e}"
            ) from e
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: EventName must belong to the enum selected in the EventType.

        """
        # Implement check for axiom 1"
        return self

    @model_validator(mode="before")
    @classmethod
    def translate_enums(cls, data: dict) -> dict:
        if "EventTypeGtEnumSymbol" in data:
            data["EventType"] = FsmEventType.symbol_to_value(
                data["EventTypeGtEnumSymbol"]
            )
            del data["EventTypeGtEnumSymbol"]
        return data

    @classmethod
    def from_dict(cls, d: dict) -> "FsmEvent":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "FsmEvent":
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
        d["EventType"] = self.event_type.value
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the fsm.event.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    @classmethod
    def type_name_value(cls) -> str:
        return "fsm.event"
