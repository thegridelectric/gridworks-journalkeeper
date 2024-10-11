"""Type fsm.event, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import (
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
from gjk.property_format import (
    HandleName,
    UTCMilliseconds,
    UUID4Str,
)


class FsmEvent(GwBase):
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
    send_time_unix_ms: UTCMilliseconds
    type_name: Literal["fsm.event"] = "fsm.event"
    version: Literal["000"] = "000"

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
