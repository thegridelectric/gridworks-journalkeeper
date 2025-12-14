"""Type heartbeat.a, version 001"""

from typing import Literal

from gw.named_types import GwBase


class HeartbeatA(GwBase):
    type_name: Literal["heartbeat.a"] = "heartbeat.a"
    version: Literal["001"] = "001"
