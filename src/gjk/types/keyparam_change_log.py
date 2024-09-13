"""Type keyparam.change.log, version 000"""

import json
import logging
from typing import Any, Dict, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)

from gjk.enums import KindOfParam
from gjk.property_format import (
    LeftRightDot,
    check_is_log_style_date_with_millis,
)

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class KeyparamChangeLog(BaseModel):
    """
    Key Param Change Record.

    The keyparam.change.record type is designed for straightforward logging of important parameter
    changes in the SCADA and AtomicTNode code for transactive space-heating systems. Check out
    the details in [gridworks-atn]( https://github.com/thegridelectric/gridworks-atn) and [gw-scada-spaceheat-python](https://github.com/thegridelectric/gw-scada-spaceheat-python).
    It's made for humans—developers and system maintainers—to easily create and reference records
    of significant changes. Keep it short and sweet. We suggest using a "Before" and "After"
    attribute pattern to include the changed value, focusing for example on specific components
    rather than the entire hardware layout.
    """

    about_node_alias: LeftRightDot
    change_time_utc: str
    author: str
    param_name: str
    description: str
    kind: KindOfParam
    type_name: Literal["keyparam.change.log"] = "keyparam.change.log"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
    )

    @field_validator("change_time_utc")
    @classmethod
    def _check_change_time_utc(cls, v: str) -> str:
        try:
            check_is_log_style_date_with_millis(v)
        except ValueError as e:
            raise ValueError(
                f"ChangeTimeUtc failed LogStyleDateWithMillis format validation: {e}",
            ) from e
        return v

    @model_validator(mode="before")
    @classmethod
    def translate_enums(cls, data: dict) -> dict:
        if "KindGtEnumSymbol" in data:
            data["Kind"] = KindOfParam.symbol_to_value(data["KindGtEnumSymbol"])
            del data["KindGtEnumSymbol"]
        return data

    @classmethod
    def from_dict(cls, d: dict) -> "KeyparamChangeLog":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "KeyparamChangeLog":
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing must result in dict!\n <{b}>")
        return cls.from_dict(d)

    def to_dict(self) -> Dict[str, Any]:
        """
        Handles lists of enums differently than model_dump
        """
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["Kind"] = self.kind.value
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the keyparam.change.log.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    @classmethod
    def type_name_value(cls) -> str:
        return "keyparam.change.log"
