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
    model_validator,
)
from typing_extensions import Self

from gjk.enums import (
    ChangeAquastatControl,
    ChangeHeatcallSource,
    ChangeHeatPumpControl,
    ChangeLgOperatingMode,
    ChangePrimaryPumpControl,
    ChangePrimaryPumpState,
    ChangeRelayPin,
    ChangeRelayState,
    ChangeStoreFlowDirection,
    ChangeValveState,
    FsmEventType,
)
from gjk.type_helpers.property_format import (
    HandleName,
    ReasonableUnixMs,
    UUID4Str,
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

    from_handle: HandleName
    to_handle: HandleName
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

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: EventName must belong to the enum selected in the EventType.

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
