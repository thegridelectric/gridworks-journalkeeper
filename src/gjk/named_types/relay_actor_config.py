"""Type relay.actor.config, version 002"""

from typing import Literal, Optional

from gw.named_types import GwBase
from pydantic import PositiveInt, StrictInt, model_validator
from typing_extensions import Self

from gjk.enums import RelayWiringConfig, Unit
from gjk.property_format import (
    SpaceheatName,
)


class RelayActorConfig(GwBase):
    relay_idx: PositiveInt
    actor_name: SpaceheatName
    wiring_config: RelayWiringConfig
    event_type: str
    de_energizing_event: str
    energizing_event: str
    state_type: str
    de_energized_state: str
    energized_state: str
    channel_name: SpaceheatName
    poll_period_s: Optional[PositiveInt] = None
    capture_period_s: PositiveInt
    async_capture: bool
    async_capture_delta: Optional[PositiveInt] = None
    exponent: StrictInt
    unit: Unit
    type_name: Literal["relay.actor.config"] = "relay.actor.config"
    version: Literal["002"] = "002"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: EventType, DeEnergizingEvent/EnergizingEvent consistency.
        If the event type is the name of a known enum, then the DeEnergizingEvent, EnergizingEvent pair are the values of that enum.
        """
        # Implement check for axiom 1"
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: StateType, EnergizedState/DeEnergizedState consistency.
        If the state type is the name of a known enum, then the DeEnergizedState, EnergizedState pair are the values of that enum.
        """
        # Implement check for axiom 2"
        return self

    @model_validator(mode="after")
    def check_axiom_3(self) -> Self:
        """
        Axiom 3: Events and States match. .
         E.g. if RelayOpen is the EnergizedState then the EnergizingEvent is OpenRelay.
        """
        # Implement check for axiom 3"
        return self
