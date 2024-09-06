"""Type telemetry.snapshot.spaceheat, version 000"""

import json
import logging
from typing import Any, Dict, List, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from gjk.enums import TelemetryName
from gjk.type_helpers.property_format import (
    LeftRightDotStr,
    check_is_reasonable_unix_time_ms,
)

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class TelemetrySnapshotSpaceheat(BaseModel):
    """
    Snapshot of Telemetry Data from a SpaceHeat SCADA.

    A snapshot of all current sensed states, sent from a spaceheat SCADA to its AtomicTNode.
    The nth element of each of the three lists refer to the same reading (i.e., what is getting
    read, what the value is, what the TelemetryNames are.)

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/spaceheat-node.html)
    """

    report_time_unix_ms: int
    about_node_alias_list: List[LeftRightDotStr]
    value_list: List[int]
    telemetry_name_list: List[TelemetryName]
    type_name: Literal["telemetry.snapshot.spaceheat"] = "telemetry.snapshot.spaceheat"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        populate_by_name=True,
    )

    @field_validator("report_time_unix_ms")
    @classmethod
    def _check_report_time_unix_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"ReportTimeUnixMs failed ReasonableUnixTimeMs format validation: {e}",
            ) from e
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: ListLengthConsistency.
        AboutNodeAliastList, ValueList and TelemetryNameList must all have the same length.
        """
        # Implement check for axiom 1"
        return self

    @model_validator(mode="before")
    @classmethod
    def translate_enums(cls, data: dict) -> dict:
        if "TelemetryNameList" in data:
            if not isinstance(data["TelemetryNameList"], list):
                raise GwTypeError("TelemetryNameList must be a list!")
            nl = []
            for elt in data["TelemetryNameList"]:
                if elt in TelemetryName.values():
                    nl.append(elt)
                elif elt in TelemetryName.symbols():
                    nl.append(TelemetryName.symbol_to_value(elt))
                else:
                    nl.append(TelemetryName.default())
            data["TelemetryNameList"] = nl
        return data

    @classmethod
    def from_dict(cls, d: dict) -> "TelemetrySnapshotSpaceheat":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "TelemetrySnapshotSpaceheat":
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
        return self.plain_enum_dict()

    def plain_enum_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["TelemetryNameList"] = [elt.value for elt in self.telemetry_name_list]
        return d

    def enum_encoded_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["TelemetryNameList"] = [
            TelemetryName.value_to_symbol(elt.value) for elt in self.telemetry_name_list
        ]
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the telemetry.snapshot.spaceheat.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    def __hash__(self) -> int:
        # Can use as keys in dicts
        return hash(type(self), *tuple(self.__dict__.values()))
