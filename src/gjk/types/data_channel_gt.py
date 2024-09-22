"""Type data.channel.gt, version 001"""

import json
import logging
from typing import Any, Dict, Literal, Optional

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    model_validator,
)
from typing_extensions import Self

from gjk.enums import TelemetryName
from gjk.property_format import (
    LeftRightDot,
    SpaceheatName,
    UTCSeconds,
    UUID4Str,
)

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class DataChannelGt(BaseModel):
    """
    Data Channel.

    Core mechanism for identifying a stream of telemetry data. Everything but the
    DisplayName and StartS are meant to be immutable. The Name is meant to be unique
    per TerminalAssetAlias.
    """

    name: SpaceheatName
    display_name: str
    about_node_name: SpaceheatName
    captured_by_node_name: SpaceheatName
    telemetry_name: TelemetryName
    terminal_asset_alias: LeftRightDot
    in_power_metering: Optional[bool] = None
    start_s: Optional[UTCSeconds] = None
    id: UUID4Str
    type_name: Literal["data.channel.gt"] = "data.channel.gt"
    version: Literal["001"] = "001"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        frozen=True,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Power Metering.
        If InPowerMetering is true then the TelemetryName must be PowerW
        """
        if self.in_power_metering and self.telemetry_name != TelemetryName.PowerW:
            raise ValueError(
                "Axiom 1 failed!  If InPowerMetering is true "
                f"then the TelemetryName must be PowerW: {self.to_dict()} "
            )
        return self

    @model_validator(mode="before")
    @classmethod
    def translate_enums(cls, data: dict) -> dict:
        if "TelemetryNameGtEnumSymbol" in data:
            data["TelemetryName"] = TelemetryName.symbol_to_value(
                data["TelemetryNameGtEnumSymbol"]
            )
            del data["TelemetryNameGtEnumSymbol"]
        return data

    @classmethod
    def from_dict(cls, d: dict) -> "DataChannelGt":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "DataChannelGt":
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
        d["TelemetryName"] = self.telemetry_name.value
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the data.channel.gt.001 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    def to_sql_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["telemetry_name"] = self.telemetry_name.value
        d.pop("type_name", None)
        d.pop("version", None)
        return d

    @classmethod
    def type_name_value(cls) -> str:
        return "data.channel.gt"
