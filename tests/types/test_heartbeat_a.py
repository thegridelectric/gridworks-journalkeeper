"""Tests heartbeat.a type, version 001"""

from gjk.types import HeartbeatA


def test_heartbeat_a_generated() -> None:
    t = HeartbeatA()

    d = {
        "TypeName": "heartbeat.a",
        "Version": "001",
    }

    assert t.to_dict() == d
    assert t == HeartbeatA.from_dict(d)
