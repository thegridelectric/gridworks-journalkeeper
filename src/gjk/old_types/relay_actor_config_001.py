"""Type relay.actor.config, version 001"""

from typing import Literal, Optional

from gw.named_types import GwBase
from pydantic import PositiveInt, StrictInt

from gjk.enums import RelayWiringConfig, Unit
from gjk.property_format import (
    SpaceheatName,
)


class RelayActorConfig001(GwBase):
    relay_idx: PositiveInt
    actor_name: SpaceheatName
    wiring_config: RelayWiringConfig
    event_type: str
    de_energizing_event: str
    energizing_event: str
    channel_name: SpaceheatName
    poll_period_s: Optional[PositiveInt] = None
    capture_period_s: PositiveInt
    async_capture: bool
    async_capture_delta: Optional[PositiveInt] = None
    exponent: StrictInt
    unit: Unit
    type_name: Literal["relay.actor.config"] = "relay.actor.config"
    version: Literal["001"] = "001"
