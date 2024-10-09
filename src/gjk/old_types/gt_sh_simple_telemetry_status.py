"""Type gt.sh.simple.telemetry.status, version 100"""

from typing import List, Literal

from pydantic import StrictInt, model_validator
from typing_extensions import Self

from gjk.enums import TelemetryName
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
)
from gjk.types.gw_base import GwBase


class GtShSimpleTelemetryStatus(GwBase):
    sh_node_alias: LeftRightDot
    telemetry_name: TelemetryName
    value_list: List[StrictInt]
    read_time_unix_ms_list: List[UTCMilliseconds]
    type_name: Literal["gt.sh.simple.telemetry.status"] = (
        "gt.sh.simple.telemetry.status"
    )
    version: Literal["100"] = "100"

    @model_validator(mode="before")
    @classmethod
    def translate_enums(cls, data: dict) -> dict:
        if "TelemetryNameGtEnumSymbol" in data:
            data["TelemetryName"] = TelemetryName.symbol_to_value(
                data["TelemetryNameGtEnumSymbol"]
            )
            del data["TelemetryNameGtEnumSymbol"]
        return data

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: ListLengthConsistency.
        ValueList and ReadTimeUnixMsList must have the same length.
        """
        # Implement check for axiom 1"
        return self
