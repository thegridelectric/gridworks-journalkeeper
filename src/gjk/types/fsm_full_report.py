"""Type fsm.full.report, version 000"""

from typing import List, Literal

from gjk.property_format import (
    SpaceheatName,
    UUID4Str,
)
from gjk.types.fsm_atomic_report import FsmAtomicReport
from gjk.types.gw_base import GwBase


class FsmFullReport(GwBase):
    """
    There will be cascading events, actions and transitions that will naturally follow a single
    high-level event. This message is designed to encapsulate all of those.

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/finite-state-machines.html)
    """

    from_name: SpaceheatName
    trigger_id: UUID4Str
    atomic_list: List[FsmAtomicReport]
    type_name: Literal["fsm.full.report"] = "fsm.full.report"
    version: Literal["000"] = "000"
