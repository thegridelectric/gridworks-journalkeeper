import struct
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class Dispatch(BaseModel):
    turn_on_or_off: int
    type_name: Literal["d"] = "d"
    model_config = ConfigDict(
        populate_by_name=True, alias_generator=snake_to_pascal, extra="forbid"
    )

    @field_validator("turn_on_or_off")
    @classmethod
    def check_turn_on_or_off(cls, v: int) -> str:
        if v not in {0, 1}:
            raise ValueError(f"TurnOnOrOff must be 0 or 1, not {v}")
        return v

    def to_type(self) -> bytes:
        return struct.pack("<h", self.turn_on_or_off)

    @classmethod
    def from_type(cls, b: bytes) -> "Dispatch":
        try:
            turn_on_or_off = struct.unpack("<h", b)[0]
        except Exception as e:
            raise GwTypeError(f"bytes failed struct.unpack('<h', b): {b}") from e
        try:
            t = Dispatch(turn_on_or_off=turn_on_or_off)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error {e}") from e
        return t

    @classmethod
    def type_name_value(cls) -> str:
        return "d"
