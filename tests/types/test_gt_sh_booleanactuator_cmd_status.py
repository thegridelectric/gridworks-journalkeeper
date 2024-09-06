"""Tests gt.sh.booleanactuator.cmd.status type, version 101"""

from gjk.types import GtShBooleanactuatorCmdStatus


def test_gt_sh_booleanactuator_cmd_status_generated() -> None:
    t = GtShBooleanactuatorCmdStatus(
        sh_node_name="a.elt1.relay",
        relay_state_command_list=[0],
        command_time_unix_ms_list=[1656443704800],
    )

    d = {
        "ShNodeName": "a.elt1.relay",
        "RelayStateCommandList": [0],
        "CommandTimeUnixMsList": [1656443704800],
        "TypeName": "gt.sh.booleanactuator.cmd.status",
        "Version": "101",
    }

    assert t.to_dict() == d
    assert t == GtShBooleanactuatorCmdStatus.from_dict(d)
