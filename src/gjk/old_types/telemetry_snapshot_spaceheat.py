"""Type telemetry.snapshot.spaceheat, version 000"""

from typing import List, Literal

from gw.errors import GwTypeError
from gw.named_types import GwBase
from pydantic import StrictInt, model_validator
from typing_extensions import Self

from gjk.enums import TelemetryName
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
)


class TelemetrySnapshotSpaceheat(GwBase):
    report_time_unix_ms: UTCMilliseconds
    about_node_alias_list: List[LeftRightDot]
    value_list: List[StrictInt]
    telemetry_name_list: List[TelemetryName]
    type_name: Literal["telemetry.snapshot.spaceheat"] = "telemetry.snapshot.spaceheat"
    version: Literal["000"] = "000"

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
