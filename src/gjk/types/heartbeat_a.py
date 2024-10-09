"""Type heartbeat.a, version 001"""

from typing import Literal

from gjk.types.gw_base import GwBase


class HeartbeatA(GwBase):
    type_name: Literal["heartbeat.a"] = "heartbeat.a"
    version: Literal["001"] = "001"
