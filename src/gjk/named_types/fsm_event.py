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
    ChangePrimaryPumpControl,
    ChangeRelayPin,
    ChangeRelayState,
    ChangeValveState,
)
from gjk.property_format import (
    HandleName,
    UTCMilliseconds,
    UUID4Str,
    LeftRightDot
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
    event_type:LeftRightDot
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
        return self
