"""Type gt.sh.simple.telemetry.status, version 100"""

import json
import logging
from typing import Any, Dict, List, Literal

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
    ReallyAnInt,
    UTCMilliseconds,
)

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GtShSimpleTelemetryStatus(BaseModel):
    """
    Data read from a SimpleSensor run by a SpaceHeat SCADA.

    A list of readings from a simple sensor for a Spaceheat SCADA. Designed as part of a status
    message sent from the SCADA to its AtomicTNode typically once every 5 minutes. The nth element
    of each of its two lists refer to the same reading (i.e. what the value is, when it was
    read).

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/simple-sensor.html)
    """

    sh_node_alias: LeftRightDot
    telemetry_name: TelemetryName
    value_list: List[ReallyAnInt]
    read_time_unix_ms_list: List[UTCMilliseconds]
    type_name: Literal["gt.sh.simple.telemetry.status"] = (
        "gt.sh.simple.telemetry.status"
    )
    version: Literal["100"] = "100"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        frozen=True,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: ListLengthConsistency.
        ValueList and ReadTimeUnixMsList must have the same length.
        """
        # Implement check for axiom 1"
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
    def from_dict(cls, d: dict) -> "GtShSimpleTelemetryStatus":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "GtShSimpleTelemetryStatus":
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
        Serialize to the gt.sh.simple.telemetry.status.100 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    @classmethod
    def type_name_value(cls) -> str:
        return "gt.sh.simple.telemetry.status"
