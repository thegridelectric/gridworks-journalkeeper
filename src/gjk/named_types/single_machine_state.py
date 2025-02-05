"""Type single.machine.state, version 000"""

from typing import Literal, Optional

from gw.named_types import GwBase
from pydantic import model_validator
from typing_extensions import Self

from gjk.property_format import (
    HandleName,
    LeftRightDot,
    UTCMilliseconds,
)


class SingleMachineState(GwBase):
    machine_handle: HandleName
    state_enum: LeftRightDot
    state: str
    unix_ms: UTCMilliseconds
    cause: Optional[str] = None
    type_name: Literal["single.machine.state"] = "single.machine.state"
    version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: If StateEnum is a recongized enum, then State is a value of that enum.
        """
        # Implement check for axiom 1"
        return self
