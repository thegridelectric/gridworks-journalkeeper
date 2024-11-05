"""Type gridworks.event.problem, version 001"""

from typing import Literal

from gw.named_types import GwBase

from gjk.enums import ProblemType
from gjk.property_format import (
    UTCMilliseconds,
    UUID4Str,
)


class GridworksEventProblem(GwBase):
    src: str
    problem_type: ProblemType
    summary: str
    details: str
    time_created_ms: UTCMilliseconds
    message_id: UUID4Str
    type_name: Literal["gridworks.event.problem"] = "gridworks.event.problem"
    version: Literal["001"] = "001"
