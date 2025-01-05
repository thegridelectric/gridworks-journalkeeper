"""Tests machine.states type, version 000"""

from gjk.named_types import MachineStates


def test_machine_states_generated() -> None:
    d = {
        "MachineHandle": "auto.pico-cycler",
        "StateEnum": "pico.cycler.state",
        "StateList": ["PicosLive"],
        "UnixMsList": [1731168353695],
        "TypeName": "machine.states",
        "Version": "000",
    }

    assert MachineStates.from_dict(d).to_dict() == d
