import struct
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

MAX_SHORT = 32767


class Power(BaseModel):
    value: int
    type_name: Literal["p"] = "p"
    model_config = ConfigDict(
        populate_by_name=True, alias_generator=snake_to_pascal, extra="forbid"
    )

    @field_validator("value")
    @classmethod
    def check_value(cls, v: int) -> str:
        if v < -MAX_SHORT or v > MAX_SHORT:
            raise ValueError(f"value needs to be a short! Between +/- {MAX_SHORT}")
        return v

    def to_type(self) -> bytes:
        return struct.pack("<h", self.value)

    @classmethod
    def from_type(cls, b: bytes) -> "Power":
        try:
            value = struct.unpack("<h", b)[0]
        except Exception as e:
            raise GwTypeError(f"bytes failed struct.unpack('<h', b): {b}") from e
        try:
            t = Power(value=value)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def type_name_value(cls) -> str:
        return "p"
