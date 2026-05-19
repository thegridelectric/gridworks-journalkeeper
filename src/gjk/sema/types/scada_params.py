from typing import Literal

from pydantic import ConfigDict

from gjk.sema.base import SemaType
from gjk.sema.property_format import (
    LeftRightDot,
    SpaceheatName,
    UTCMilliseconds,
    UUID4Str,
)
from gjk.sema.types.ha1_params import Ha1Params


class ScadaParams(SemaType):
    """Sema: https://schemas.electricity.works/types/scada.params/005"""

    from_g_node_alias: LeftRightDot
    from_name: SpaceheatName
    to_name: SpaceheatName
    unix_time_ms: UTCMilliseconds
    message_id: UUID4Str
    new_params: Ha1Params | None = None
    old_params: Ha1Params | None = None
    type_name: Literal["scada.params"] = "scada.params"
    version: Literal["005"] = "005"

    model_config = ConfigDict(**(SemaType.model_config | {"extra": "allow"}))
