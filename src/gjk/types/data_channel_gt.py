"""Type data.channel.gt, version 001"""

from typing import Any, Dict, Literal, Optional

from pydantic import (
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
from gjk.types.gw_base import GwBase


class DataChannelGt(GwBase):
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

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Power Metering.
        If InPowerMetering is true then the TelemetryName must be PowerW
        """
        if self.in_power_metering and self.telemetry_name != TelemetryName.PowerW:
            raise ValueError(
                "Axiom 1 failed!  If InPowerMetering is true "
                f"then the TelemetryName must be PowerW: {self.model_dump()} "
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

    def to_sql_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d.pop("type_name", None)
        d.pop("version", None)
        return d
