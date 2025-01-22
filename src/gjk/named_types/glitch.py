"""Type glitch, version 000"""

from typing import Literal

from gw.named_types import GwBase

from gjk.enums import LogLevel
from gjk.property_format import (
    LeftRightDot,
    SpaceheatName,
    UTCMilliseconds,
)


class Glitch(GwBase):
    from_g_node_alias: LeftRightDot
    node: SpaceheatName
    type: LogLevel
    summary: str
    details: str
    created_ms: UTCMilliseconds
    type_name: Literal["glitch"] = "glitch"
    version: Literal["000"] = "000"
