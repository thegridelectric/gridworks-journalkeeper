"""Type pico.tank.module.component.gt, version 000"""

from typing import List, Literal, Optional

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import ConfigDict, PositiveInt, StrictInt, model_validator
from typing_extensions import Self

from gjk.enums import TempCalcMethod
from gjk.named_types.channel_config import ChannelConfig
from gjk.property_format import (
    UUID4Str,
)


class PicoTankModuleComponentGt(GwBase):
    enabled: bool
    pico_hw_uid : str | None = None
    pico_a_hw_uid: str | None = None
    pico_b_hw_uid: str | None = None
    temp_calc_method: TempCalcMethod
    thermistor_beta: PositiveInt
    send_micro_volts: bool
    samples: PositiveInt
    num_sample_averages: PositiveInt
    pico_k_ohms: PositiveInt | None = None
    component_id: UUID4Str
    component_attribute_class_id: UUID4Str
    config_list: List[ChannelConfig]
    display_name: Optional[str] = None
    serial_number: str
    async_capture_delta_micro_volts: StrictInt
    sensor_order: list[int] | None = None
    type_name: Literal["pico.tank.module.component.gt"] = (
        "pico.tank.module.component.gt"
    )
    version: Literal["011"] = "011"

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
        Axiom 1: PicoHwUid exists  XOR (both PicoAHwUid and PicoBHwUid exist)
        """
        if self.pico_hw_uid is not None:
            if self.pico_a_hw_uid or self.pico_b_hw_uid:
                raise ValueError(
                    "Can't have both PicoHwUid and any of (PicoAHwUid, PicoBHwUid"
                )
        elif not (self.pico_a_hw_uid and self.pico_b_hw_uid):
            raise ValueError(
                "If PicoHwUid is not set, PicoAHwUid and PicoBHwUid must both be set!"
            )

        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: PicoKOhms exists iff TempCalcMethod is TempCalcMethod.SimpleBetaForPico
        # note this is a known incorrect method, but there are a few in the field
        # that do this.
        """
        is_simple_beta = self.temp_calc_method == TempCalcMethod.SimpleBetaForPico
        has_kohms = self.pico_k_ohms is not None

        if is_simple_beta != has_kohms:
            raise ValueError(
                "PicoKOhms must be provided if and only if TempCalcMethod is SimpleBetaForPico"
            )

        return self

    def check_axiom_3(self) -> None:
        """
        Axiom 3:
        If SensorOrder is provided, it must be a permutation of [1, 2, 3].
        """
        if self.sensor_order is None:
            return

        expected = [1, 2, 3]
        order = self.sensor_order

        # Must be length 3
        if len(order) != 3:
            raise ValueError(f"SensorOrder must be length 3 if provided; got {order}")

        # Must contain exactly the integers 1, 2, 3 with no duplicates
        if sorted(order) != expected:
            raise ValueError(
                f"SensorOrder must be a permutation of {expected}; got {order}"
            )
