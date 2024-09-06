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
    field_validator,
    model_validator,
)
from typing_extensions import Self

from gjk.enums import FsmActionType, FsmEventType, FsmName, FsmReportType
from gjk.type_helpers.property_format import (
    UUID4Str,
    check_is_handle_name,
    check_is_reasonable_unix_time_ms,
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

    from_handle: str
    about_fsm: FsmName
    report_type: FsmReportType
    action_type: Optional[FsmActionType] = None
    action: Optional[int] = None
    event_type: Optional[FsmEventType] = None
    event: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    unix_time_ms: int
    trigger_id: UUID4Str
    type_name: Literal["fsm.atomic.report"] = "fsm.atomic.report"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
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

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Action and ActionType exist iff  ReportType is Action.
        The Optional Attributes ActionType and Action exist if and only if IsAction is true.
        """
        # Implement check for axiom 1"
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: If Action exists, then it belongs to the un-versioned enum selected in the ActionType.

        """
        # Implement check for axiom 2"
        return self

    @model_validator(mode="after")
    def check_axiom_3(self) -> Self:
        """
        Axiom 3: EventType, Event, FromState, ToState exist iff ReportType is Event.

        """
        # Implement check for axiom 3"
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
        return self.plain_enum_dict()

    def plain_enum_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["AboutFsm"] = self.about_fsm.value
        d["ReportType"] = self.report_type.value
        if "ActionType" in d:
            d["ActionType"] = d["ActionType"].value
        if "EventType" in d:
            d["EventType"] = d["EventType"].value
        return d

    def enum_encoded_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        del d["AboutFsm"]
        d["AboutFsmGtEnumSymbol"] = FsmName.value_to_symbol(self.about_fsm)
        del d["ReportType"]
        d["ReportTypeGtEnumSymbol"] = FsmReportType.value_to_symbol(self.report_type)
        if "ActionType" in d:
            del d["ActionType"]
            d["ActionTypeGtEnumSymbol"] = FsmActionType.value_to_symbol(
                self.action_type
            )
        if "EventType" in d:
            del d["EventType"]
            d["EventTypeGtEnumSymbol"] = FsmEventType.value_to_symbol(self.event_type)
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the fsm.atomic.report.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    def __hash__(self) -> int:
        # Can use as keys in dicts
        return hash(type(self), *tuple(self.__dict__.values()))
