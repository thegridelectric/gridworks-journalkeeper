"""Type scada.params, version 003"""

from typing import Literal, Optional

from gw.named_types import GwBase

from gjk.named_types.ha1_params import Ha1Params
from gjk.property_format import (
    LeftRightDot,
    SpaceheatName,
    UTCMilliseconds,
    UUID4Str,
)


class ScadaParams(GwBase):
    from_g_node_alias: LeftRightDot
    from_name: SpaceheatName
    to_name: SpaceheatName
    unix_time_ms: UTCMilliseconds
    message_id: UUID4Str
    new_params: Ha1Params | None = None
    old_params: Ha1Params | None = None
    type_name: Literal["scada.params"] = "scada.params"
    version: Literal["004"] = "004"
