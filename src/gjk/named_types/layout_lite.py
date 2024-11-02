"""Type layout.lite, version 000"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import PositiveInt

from gjk.named_types.data_channel_gt import DataChannelGt
from gjk.named_types.pico_flow_module_component_gt import PicoFlowModuleComponentGt
from gjk.named_types.pico_tank_module_component_gt import PicoTankModuleComponentGt
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UUID4Str,
)


class LayoutLite(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    message_created_ms: UTCMilliseconds
    message_id: UUID4Str
    strategy: str
    zone_list: List[str]
    total_store_tanks: PositiveInt
    data_channels: List[DataChannelGt]
    tank_module_components: List[PicoTankModuleComponentGt]
    flow_module_components: List[PicoFlowModuleComponentGt]
    type_name: Literal["layout.lite"] = "layout.lite"
    version: Literal["000"] = "000"
