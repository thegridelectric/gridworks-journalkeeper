"""Type layout.lite, version 004"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import PositiveInt

from gjk.named_types.data_channel_gt import DataChannelGt
from gjk.named_types.ha1_params import Ha1Params
from gjk.named_types.i2c_multichannel_dt_relay_component_gt import (
    I2cMultichannelDtRelayComponentGt,
)
from gjk.named_types.pico_flow_module_component_gt import PicoFlowModuleComponentGt
from gjk.named_types.pico_tank_module_component_gt import PicoTankModuleComponentGt
from gjk.named_types.spaceheat_node_gt import SpaceheatNodeGt
from gjk.named_types.synth_channel_gt import SynthChannelGt
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
    sh_nodes: List[SpaceheatNodeGt]
    data_channels: List[DataChannelGt]
    synth_channels: List[SynthChannelGt]
    tank_module_components: List[PicoTankModuleComponentGt]
    flow_module_components: List[PicoFlowModuleComponentGt]
    ha1_params: Ha1Params
    i2c_relay_component: I2cMultichannelDtRelayComponentGt
    type_name: Literal["layout.lite"] = "layout.lite"
    version: Literal["001","002","003","004"] = "004"
