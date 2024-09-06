"""Tests gt.sh.booleanactuator.cmd.status type, version 101"""

from gjk.types import GtShBooleanactuatorCmdStatus


def test_gt_sh_booleanactuator_cmd_status_generated() -> None:
    d = {
        "ShNodeName": "a.elt1.relay",
        "RelayStateCommandList": [0],
        "CommandTimeUnixMsList": [1656443704800],
        "TypeName": "gt.sh.booleanactuator.cmd.status",
        "Version": "101",
    }

    t = GtShBooleanactuatorCmdStatus.from_dict(d)
    assert t.to_dict() == d

