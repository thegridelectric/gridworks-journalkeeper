from typing import Literal
from pydantic import StrictInt, model_validator
from gjk.sema.base import SemaType
from gjk.sema.enums import ChangeRelayState
from gjk.sema.enums import RelayWiringConfig
from gjk.sema.enums import SpaceheatUnit
from gjk.sema.property_format import LeftRightDot
from gjk.sema.property_format import NonEmptyString
from gjk.sema.property_format import PositiveInt
from gjk.sema.property_format import SpaceheatName
from gjk.sema.types.relay_actor_config import RelayActorConfig


class RelayActorConfig001(SemaType):
    """Sema: https://schemas.electricity.works/types/relay.actor.config/001"""

    channel_name: SpaceheatName
    poll_period_ms: PositiveInt | None = None
    capture_period_s: PositiveInt
    async_capture: bool
    async_capture_delta: PositiveInt | None = None
    exponent: StrictInt
    unit: SpaceheatUnit
    relay_idx: PositiveInt
    actor_name: SpaceheatName
    wiring_config: RelayWiringConfig
    event_type: LeftRightDot
    de_energizing_event: NonEmptyString
    energizing_event: NonEmptyString
    type_name: Literal["relay.actor.config"] = "relay.actor.config"
    version: Literal["001"] = "001"

    @model_validator(mode="after")
    def check_axiom_1(self) -> "RelayActorConfig001":
        """
        Axiom 1: EventEnumConsistency
        If EventType names a known enum, then DeEnergizingEvent and EnergizingEvent SHALL both
        be valid values of that enum.
        """
        if self.event_type == "change.relay.state":
            valid = set(ChangeRelayState.values())
            if (
                self.de_energizing_event not in valid
                or self.energizing_event not in valid
            ):
                raise ValueError(
                    "Axiom 1 failed: relay state events must be valid change.relay.state values."
                )
        return self

    def upgrade(self) -> RelayActorConfig:
        """
        - StateType: add
        - DeEnergizedState: add
        - EnergizedState: add
        """
        raise SemaType.upgrade_requires_context(
            "RelayActorConfig001 cannot be upgraded to "
            "RelayActorConfig without context: v002 adds the "
            "required StateType, DeEnergizedState and EnergizedState, absent from a "
            "v001 message and which SHALL NOT be fabricated."
        )
