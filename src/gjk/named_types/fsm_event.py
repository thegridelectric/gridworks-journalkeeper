"""Type fsm.event, version 000"""

from typing import Literal

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import ConfigDict, model_validator
from typing_extensions import Self

from gjk.property_format import (
    HandleName,
    LeftRightDot,
    UTCMilliseconds,
    UUID4Str,
)


class FsmEvent(GwBase):
    from_handle: HandleName
    to_handle: HandleName
    event_type: LeftRightDot
    event_name: str
    trigger_id: UUID4Str
    send_time_unix_ms: UTCMilliseconds
    type_name: Literal["fsm.event"] = "fsm.event"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: EventName must belong to the enum selected in the EventType.

        """
        # Implement check for axiom 1"
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: FromHandle must be the immediate boss of ToHandle.

        """
        # Implement check for axiom 2"
        return self
