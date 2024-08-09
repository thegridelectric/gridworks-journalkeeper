import struct
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import snake_to_pascal
from pydantic import BaseModel, field_validator

MAX_SHORT = 32767


class Power(BaseModel):
    value: int
    type_name: Literal["p"] = "p"

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal
        extra = "forbid"

    @field_validator("value")
    @classmethod
    def check_value(cls, v: int) -> str:
        if v < -MAX_SHORT or v > MAX_SHORT:
            raise ValueError(f"value needs to be a short! Between +/- {MAX_SHORT}")
        return v

    def as_type(self) -> bytes:
        return struct.pack("<h", self.value)


class PowerMaker:
    type_name = "p"

    @classmethod
    def tuple_to_type(cls, tpl: Power) -> bytes:
        return tpl.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> Power:
        try:
            value = struct.unpack("<h", b)[0]
        except Exception as e:
            raise GwTypeError(f"bytes failed struct.unpack('<h', b): {b}") from e
        tpl = Power(value=value)
        return tpl
