"""Tests heartbeat.a type, version 001"""

from gjk.named_types import HeartbeatA


def test_heartbeat_a_generated() -> None:
    d = {
        "TypeName": "heartbeat.a",
        "Version": "001",
    }

    assert HeartbeatA.from_dict(d).to_dict() == d
