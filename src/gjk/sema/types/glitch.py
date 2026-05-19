from typing import Literal

from gjk.sema.base import SemaType
from gjk.sema.enums import LogLevel
from gjk.sema.property_format import LeftRightDot, SpaceheatName, UTCMilliseconds


class Glitch(SemaType):
    """Sema: https://schemas.electricity.works/types/glitch/000"""

    from_g_node_alias: LeftRightDot
    node: SpaceheatName
    type: LogLevel
    summary: str
    details: str
    created_ms: UTCMilliseconds
    type_name: Literal["glitch"] = "glitch"
    version: Literal["000"] = "000"
