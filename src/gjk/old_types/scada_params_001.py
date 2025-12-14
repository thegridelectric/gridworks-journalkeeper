"""Type scada.params, version 001"""

from typing import Literal, Optional

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import ConfigDict

from gjk.named_types.ha1_params import Ha1Params
from gjk.property_format import (
    LeftRightDot,
    SpaceheatName,
    UTCMilliseconds,
    UUID4Str,
)


class ScadaParams001(GwBase):
    from_g_node_alias: LeftRightDot
    from_name: SpaceheatName
    to_name: SpaceheatName
    unix_time_ms: UTCMilliseconds
    message_id: UUID4Str
    new_params: Optional[Ha1Params] = None
    old_params: Optional[Ha1Params] = None
    type_name: Literal["scada.params"] = "scada.params"
    version: Literal["001"] = "001"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
    )
