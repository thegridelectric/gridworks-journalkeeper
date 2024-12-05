"""Type synth.channel.gt, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import PositiveInt

from gjk.enums import TelemetryName
from gjk.property_format import (
    LeftRightDot,
    SpaceheatName,
    UUID4Str,
)


class SynthChannelGt(GwBase):
    id: UUID4Str
    name: SpaceheatName
    created_by_node_name: SpaceheatName
    telemetry_name: TelemetryName
    terminal_asset_alias: LeftRightDot
    strategy: str
    display_name: str
    sync_report_minutes: PositiveInt
    type_name: Literal["synth.channel.gt"] = "synth.channel.gt"
    version: Literal["000"] = "000"
