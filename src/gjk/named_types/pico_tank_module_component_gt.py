"""Type pico.tank.module.component.gt, version 000"""

from typing import List, Literal, Optional

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import ConfigDict, PositiveInt

from gjk.enums import TempCalcMethod
from gjk.named_types.channel_config import ChannelConfig
from gjk.property_format import (
    UUID4Str,
)


class PicoTankModuleComponentGt(GwBase):
    enabled: float
    pico_a_hw_uid: Optional[str] = None
    pico_b_hw_uid: Optional[str] = None
    temp_calc_method: TempCalcMethod
    thermistor_beta: PositiveInt
    send_micro_volts: bool
    samples: PositiveInt
    num_sample_averages: PositiveInt
    pico_k_ohms: PositiveInt
    component_id: UUID4Str
    component_attribute_class_id: UUID4Str
    config_list: List[ChannelConfig]
    display_name: Optional[str] = None
    serial_number: str
    type_name: Literal["pico.tank.module.component.gt"] = "pico.tank.module.component.gt"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal, extra="allow", frozen=True, populate_by_name=True, use_enum_values=True
    )
