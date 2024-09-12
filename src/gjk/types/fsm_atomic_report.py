"""Type fsm.atomic.report, version 000"""

import json
import logging
from typing import Any, Dict, Literal, Optional

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    model_validator,
)
from typing_extensions import Self

from gjk.enums import FsmActionType, FsmEventType, FsmName, FsmReportType
from gjk.type_helpers.property_format import (
    HandleName,
    ReallyAnInt,
    ReasonableUnixMs,
    UUID4Str,
)

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

    from_handle: HandleName
    about_fsm: FsmName
    report_type: FsmReportType
    action_type: Optional[FsmActionType] = None
    action: Optional[ReallyAnInt] = None
    event_type: Optional[FsmEventType] = None
    event: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    unix_time_ms: ReasonableUnixMs
    trigger_id: UUID4Str
    type_name: Literal["fsm.atomic.report"] = "fsm.atomic.report"
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
        Axiom 1: Action and ActionType exist iff  ReportType is Action.
        The Optional Attributes ActionType and Action exist if and only if IsAction is true.
        """
        if self.report_type == FsmReportType.Action:
            if (self.action is None) or (self.action_type is None):
                raise ValueError(
                    "ReportType is Action! Action and ActionType must both exist"
                )
        elif self.action:
            raise ValueError("ReportType is NOT Action, so Action should not exist!")
        elif self.action_type:
            raise ValueError(
                "ReportType is NOT Action, so ActionType should not exist!"
            )
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: If Action exists, then it belongs to the un-versioned enum selected in the ActionType.

        """
        if (
            self.action is not None
            and self.action_type == FsmActionType.RelayPinSet
            and self.action not in {0, 1}
        ):
            raise ValueError("ActionType RelayPinSet requires an action of 0 or 1")
        return self

    @model_validator(mode="after")
    def check_axiom_3(self) -> Self:
        """
        Axiom 3: EventType, Event, FromState, ToState exist iff ReportType is Event.

        """
        if self.report_type == FsmReportType.Event:
            if (
                not self.event_type
                or not self.event
                or not self.from_state
                or not self.to_state
            ):
                raise ValueError(
                    "ReportType is Event =>  EventType, Event, FromState, ToState must exist "
                )
        elif self.event_type or self.event or self.from_state or self.to_state:
            raise ValueError(
                "ReportType is NOT event => EventType, Event, FromState, ToState do not exist"
           )
        return self

    @model_validator(mode="before")
    @classmethod
    def translate_enums(cls, data: dict) -> dict:
        if "ActionTypeGtEnumSymbol" in data:
            data["ActionType"] = FsmActionType.symbol_to_value(
                data["ActionTypeGtEnumSymbol"]
            )
            del data["ActionTypeGtEnumSymbol"]
        if "EventTypeGtEnumSymbol" in data:
            data["EventType"] = FsmEventType.symbol_to_value(
                data["EventTypeGtEnumSymbol"]
            )
            del data["EventTypeGtEnumSymbol"]
        if "AboutFsmGtEnumSymbol" in data:
            data["AboutFsm"] = FsmName.symbol_to_value(data["AboutFsmGtEnumSymbol"])
            del data["AboutFsmGtEnumSymbol"]
        if "ReportTypeGtEnumSymbol" in data:
            data["ReportType"] = FsmReportType.symbol_to_value(
                data["ReportTypeGtEnumSymbol"]
            )
            del data["ReportTypeGtEnumSymbol"]
        return data

    @classmethod
    def from_dict(cls, d: dict) -> "FsmAtomicReport":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "FsmAtomicReport":
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
        d["AboutFsm"] = self.about_fsm.value
        d["ReportType"] = self.report_type.value
        if "ActionType" in d:
            d["ActionType"] = d["ActionType"].value
        if "EventType" in d:
            d["EventType"] = d["EventType"].value
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the fsm.atomic.report.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    @classmethod
    def type_name_value(cls) -> str:
        return "fsm.atomic.report"
