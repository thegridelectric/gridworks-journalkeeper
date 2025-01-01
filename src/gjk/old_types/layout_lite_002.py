"""Type layout.lite, version 002"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import PositiveInt, model_validator
from typing_extensions import Self

from gjk.named_types.data_channel_gt import DataChannelGt
from gjk.named_types.ha1_params import Ha1Params
from gjk.named_types.pico_flow_module_component_gt import PicoFlowModuleComponentGt
from gjk.named_types.pico_tank_module_component_gt import PicoTankModuleComponentGt
from gjk.named_types.spaceheat_node_gt import SpaceheatNodeGt
from gjk.named_types.synth_channel_gt import SynthChannelGt
from gjk.old_types.i2c_multichannel_dt_relay_component_gt_001 import (
    I2cMultichannelDtRelayComponentGt001,
)
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UUID4Str,
)


class LayoutLite002(GwBase):
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
    i2c_relay_component: I2cMultichannelDtRelayComponentGt001
    type_name: Literal["layout.lite"] = "layout.lite"
    version: Literal["002"] = "002"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Dc Node Consistency.
        Every AboutNodeName and CapturedByNodeName in a DataChannel belongs to an ShNode, and in addition every CapturedByNodeName does Not have ActorClass NoActor
        """
        # Implement check for axiom 1"
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: Node Handle Hierarchy Consistency.
        Every ShNode with a handle containing at least two words (separated by '.') has an immediate boss: another ShNode whose handle matches the original handle minus its last word.
        """
        # Implement check for axiom 2"
        return self
