"""Type energy.instruction, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import PositiveInt, StrictInt, field_validator, model_validator
from typing_extensions import Self

from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UTCSeconds,
)


class EnergyInstruction(GwBase):
    from_g_node_alias: LeftRightDot
    slot_start_s: UTCSeconds
    slot_duration_minutes: PositiveInt
    send_time_ms: UTCMilliseconds
    avg_power_watts: StrictInt
    type_name: Literal["energy.instruction"] = "energy.instruction"
    version: Literal["000"] = "000"

    @field_validator("slot_start_s")
    @classmethod
    def check_slot_start_s(cls, v: int) -> int:
        """
        Axiom 1: SlotStartS should fall on the top of. minutes
        """
        # Implement Axiom(s)
        return v

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: SendTime within 10 seconds of SlotStart.
        SendTimeMs should be no more than 10 seconds after SlotStartS
        """
        # Implement check for axiom 2"
        return self
