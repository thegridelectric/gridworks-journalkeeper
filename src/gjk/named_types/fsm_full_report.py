"""Type fsm.full.report, version 000"""

from typing import List, Literal

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import ConfigDict

from gjk.named_types.fsm_atomic_report import FsmAtomicReport
from gjk.property_format import (
    SpaceheatName,
    UUID4Str,
)


class FsmFullReport(GwBase):
    from_name: SpaceheatName
    trigger_id: UUID4Str
    atomic_list: List[FsmAtomicReport]
    type_name: Literal["fsm.full.report"] = "fsm.full.report"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
    )
