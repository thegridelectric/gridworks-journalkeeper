"""Tests relay.actor.config type, version 002"""

from gjk.enums import RelayWiringConfig, Unit
from gjk.named_types import RelayActorConfig


def test_relay_actor_config_generated() -> None:
    d = {
        "RelayIdx": 18,
        "ActorName": "relay18",
        "WiringConfig": "NormallyOpen",
        "EventType": "change.relay.state",
        "DeEnergizingEvent": "OpenRelay",
        "EnergizingEvent": "CloseRelay",
        "StateType": "relay.closed.or.open",
        "DeEnergizedState": "RelayOpen",
        "EnergizedState": "RelayClosed",
        "ChannelName": "stat-relay18",
        "PollPeriodS": 200,
        "CapturePeriodS": 60,
        "AsyncCapture": True,
        "AsyncCaptureDelta": 1,
        "Exponent": 0,
        "Unit": "Unitless",
        "TypeName": "relay.actor.config",
        "Version": "002",
    }

    assert RelayActorConfig.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, WiringConfig="unknown_enum_thing")
    assert RelayActorConfig.from_dict(d2).wiring_config == RelayWiringConfig.default()

    d2 = dict(d, Unit="unknown_enum_thing")
    assert RelayActorConfig.from_dict(d2).unit == Unit.default()
