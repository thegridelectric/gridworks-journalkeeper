from typing import List, Literal

from gw.named_types import GwBase
from pydantic import PositiveInt, model_validator
from typing_extensions import Self

from gjk.enums import ActorClass
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
    message_created_ms: UTCMilliseconds
    message_id: UUID4Str
    strategy: str
    zone_list: List[str]
    critical_zone_list: List[str]
    total_store_tanks: PositiveInt
    sh_nodes: List[SpaceheatNodeGt]
    data_channels: List[DataChannelGt]
    synth_channels: List[SynthChannelGt]
    tank_module_components: List[PicoTankModuleComponentGt]
    flow_module_components: List[PicoFlowModuleComponentGt]
    ha1_params: Ha1Params
    i2c_relay_component: I2cMultichannelDtRelayComponentGt
    type_name: Literal["layout.lite"] = "layout.lite"
    version: Literal["006"] = "006"

    #@model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Dc Node Consistency. Every AboutNodeName and CapturedByNodeName in a
        DataChannel belongs to an ShNode, and in addition every CapturedByNodeName does
        not have ActorClass NoActor.
        """
        for dc in self.data_channels:
            if dc.about_node_name not in [n.name for n in self.sh_nodes]:
                raise ValueError(
                    f"Axiom 1 violated: dc {dc.name} AboutNodeName {dc.about_node_name} not in ShNodes!"
                )
            captured_by_node = next(
                (n for n in self.sh_nodes if n.name == dc.captured_by_node_name), None
            )
            if not captured_by_node:
                raise ValueError(
                    f"Axiom 1 violated: dc {dc.name} CapturedByNodeName {dc.captured_by_node_name} not in ShNodes!"
                )
            if captured_by_node.actor_class == ActorClass.NoActor:
                raise ValueError(
                    f"Axiom 1 violated: dc {dc.name}'s CapturedByNode cannot have ActorClass NoActor!"
                )
        return self

    #@model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Node Handle Hierarchy Consistency. Every ShNode with a handle containing at least
        two words (separated by '.') has an immediate boss: another ShNode whose handle
        matches the original handle minus its last word.
        """
        existing_handles = {get_handle(node) for node in self.sh_nodes}
        for node in self.sh_nodes:
            handle = get_handle(node)
            if "." in handle:
                boss_handle = ".".join(handle.split(".")[:-1])
                if boss_handle not in existing_handles:
                    raise ValueError(
                        f"Axiom 2 violated: node {node.name} with handle {handle} missing"
                        " its immediate boss!"
                    )
        return self


    #@model_validator(mode="after")
    def check_axiom_3(self) -> Self:
        """
        Axiom 3: CriticalZoneList is a subset of ZoneList
        """
        zone_set = set(self.zone_list)
        for z in self.critical_zone_list:
            if z not in zone_set:
                raise ValueError(
                    f"Axiom 3 violated: Critical zone '{z}' is not present in ZoneList."
                )
        return self

def get_handle(node: SpaceheatNodeGt) -> str:
    if node.handle:
        return node.handle
    return node.name
