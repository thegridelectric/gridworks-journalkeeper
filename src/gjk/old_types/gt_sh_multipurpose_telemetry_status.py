"""Type gt.sh.multipurpose.telemetry.status, version 100"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import StrictInt, model_validator
from typing_extensions import Self

from gjk.enums import TelemetryName
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
)


class GtShMultipurposeTelemetryStatus(GwBase):
    about_node_alias: LeftRightDot
    sensor_node_alias: str
    telemetry_name: TelemetryName
    value_list: List[StrictInt]
    read_time_unix_ms_list: List[UTCMilliseconds]
    type_name: Literal["gt.sh.multipurpose.telemetry.status"] = (
        "gt.sh.multipurpose.telemetry.status"
    )
    version: Literal["100"] = "100"

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
