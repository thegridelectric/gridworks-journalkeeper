from typing import Literal

from gw.named_types import GwBase

from gjk.enums import GwUnit
from gjk.property_format import (
    LeftRightDot,
    SpaceheatName,
    UUID4Str,
)


class DerivedChannelGt(GwBase):
    id: UUID4Str
    name: SpaceheatName
    created_by_node_name: SpaceheatName
    strategy: SpaceheatName
    output_unit: GwUnit | None = None
    display_name: str
    terminal_asset_alias: LeftRightDot
    type_name: Literal["derived.channel.gt"] = "derived.channel.gt"
    version: Literal["000"] = "000"
