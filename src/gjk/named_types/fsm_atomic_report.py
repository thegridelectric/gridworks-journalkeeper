"""Type fsm.atomic.report, version 000"""

from typing import Literal, Optional

from gw.named_types import GwBase
from pydantic import StrictInt, model_validator
from typing_extensions import Self

from gjk.enums import FsmActionType, FsmEventType, FsmName, FsmReportType
from gjk.property_format import (
    HandleName,
    UTCMilliseconds,
    UUID4Str,
)


class FsmAtomicReport(GwBase):
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
    action: Optional[StrictInt] = None
    event_type: Optional[FsmEventType] = None
    event: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    unix_time_ms: UTCMilliseconds
    trigger_id: UUID4Str
    type_name: Literal["fsm.atomic.report"] = "fsm.atomic.report"
    version: Literal["000"] = "000"

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
