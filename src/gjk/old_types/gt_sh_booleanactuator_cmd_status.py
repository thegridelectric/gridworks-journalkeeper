"""Type gt.sh.booleanactuator.cmd.status, version 101"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import StrictInt, field_validator

from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
)


class GtShBooleanactuatorCmdStatus(GwBase):
    sh_node_name: LeftRightDot
    relay_state_command_list: List[StrictInt]
    command_time_unix_ms_list: List[UTCMilliseconds]
    type_name: Literal["gt.sh.booleanactuator.cmd.status"] = (
        "gt.sh.booleanactuator.cmd.status"
    )
    version: Literal["101"] = "101"

    @field_validator("relay_state_command_list")
    @classmethod
    def check_relay_state_command_list(cls, v: List[int]) -> List[int]:
        """
        Axiom : RelayStateCommandLIst must be all 0s and 1s.
        """
        # Implement Axiom(s)
        return v
