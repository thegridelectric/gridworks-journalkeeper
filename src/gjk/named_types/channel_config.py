"""Type channel.config, version 000"""

from typing import Literal, Optional

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import (
    ConfigDict,
    PositiveInt,
    StrictInt,
    model_validator,
)
from typing_extensions import Self

from gjk.enums import Unit
from gjk.property_format import (
    SpaceheatName,
)


class ChannelConfig(GwBase):
    channel_name: SpaceheatName
    poll_period_ms: Optional[PositiveInt] = None
    capture_period_s: PositiveInt
    async_capture: bool
    async_capture_delta: Optional[PositiveInt] = None
    exponent: StrictInt
    unit: Unit
    type_name: Literal["channel.config"] = "channel.config"
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
        Axiom 1: Capture and Polling Consistency.
        CapturePeriodMs (CapturePeriodS * 1000) must be larger than PollPeriodMs. If CapturePeriodMs < 10 * PollPeriodMs then CapturePeriodMs must be a multiple of PollPeriodMs.
        """
        # Implement check for axiom 1"
        return self
