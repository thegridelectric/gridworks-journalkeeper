"""Type pico.flow.module.component.gt, version 000"""

from typing import List, Literal, Optional, Self

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import (
    ConfigDict,
    PositiveInt,
    StrictInt,
    model_validator,
)

from gjk.enums import GpmFromHzMethod, HzCalcMethod, MakeModel
from gjk.named_types.channel_config import ChannelConfig
from gjk.property_format import (
    SpaceheatName,
    UUID4Str,
)


class PicoFlowModuleComponentGt(GwBase):
    enabled: bool
    serial_number: str
    flow_node_name: SpaceheatName
    flow_meter_type: MakeModel
    hz_calc_method: HzCalcMethod
    gpm_from_hz_method: GpmFromHzMethod
    constant_gallons_per_tick: float
    send_hz: bool
    send_gallons: bool
    send_tick_lists: bool
    no_flow_ms: PositiveInt
    async_capture_threshold_gpm_times100: StrictInt
    publish_empty_ticklist_after_s: PositiveInt | None = None
    publish_any_ticklist_after_s: PositiveInt | None = None
    publish_ticklist_period_s: PositiveInt | None = None
    publish_ticklist_length: PositiveInt | None = None
    exp_alpha: float | None = None
    cutoff_frequency: float | None = None
    component_id: UUID4Str | None = None
    component_attribute_class_id: UUID4Str | None = None
    config_list: list[ChannelConfig] | None = None
    d_isplay_name: str | None = None
    type_name: Literal["pico.flow.module.component.gt"] = (
        "pico.flow.module.component.gt"
    )
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
                Axiom 1: Param consistency.
                - If HzCalcMethod is BasicExpWeightedAvg then ExpAlpha must exist.
        - If HzCalcMethod is BasicButterhworth then CutoffFrequency must exist


        """
        # Implement check for axiom 1"
        return self
