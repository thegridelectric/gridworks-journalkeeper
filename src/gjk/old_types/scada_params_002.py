"""Type scada.params, version 002"""

from typing import Literal, Optional

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import ConfigDict

from gjk.old_types.ha1_params_001 import Ha1Params001
from gjk.property_format import (
    LeftRightDot,
    SpaceheatName,
    UTCMilliseconds,
    UUID4Str,
)


class ScadaParams002(GwBase):
    from_g_node_alias: LeftRightDot
    from_name: SpaceheatName
    to_name: SpaceheatName
    unix_time_ms: UTCMilliseconds
    message_id: UUID4Str
    new_params: Optional[Ha1Params001] = None
    old_params: Optional[Ha1Params001] = None
    type_name: Literal["scada.params"] = "scada.params"
    version: Literal["002"] = "002"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
    )
