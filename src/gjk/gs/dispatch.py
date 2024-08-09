import struct
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import snake_to_pascal
from pydantic import BaseModel, field_validator


class Dispatch(BaseModel):
    turn_on_or_off: int
    type_name: Literal["d"] = "d"

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal
        extra = "forbid"

    @field_validator("turn_on_or_off")
    @classmethod
    def check_turn_on_or_off(cls, v: int) -> str:
        if v not in {0, 1}:
            raise ValueError(f"TurnOnOrOff must be 0 or 1, not {v}")
        return v

    def as_type(self) -> bytes:
        return struct.pack("<h", self.turn_on_or_off)


class DispatchMaker:
    type_name = "d"

    @classmethod
    def tuple_to_type(cls, tpl: Dispatch) -> bytes:
        return tpl.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> Dispatch:
        try:
            turn_on_or_off = struct.unpack("<h", b)[0]
        except Exception as e:
            raise GwTypeError(f"bytes failed struct.unpack('<h', b): {b}") from e
        tpl = Dispatch(turn_on_or_off=turn_on_or_off)
        return tpl
