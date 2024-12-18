"""Type gridworks.event.report, version 000"""

from typing import Literal

from gw.named_types import GwBase

from gjk.old_types.report_000 import Report000
from gjk.property_format import (
    UTCMilliseconds,
    UUID4Str,
)


class GridworksEventReport(GwBase):
    message_id: UUID4Str
    time_created_ms: UTCMilliseconds
    src: str
    report: Report000
    type_name: Literal["gridworks.event.report"] = "gridworks.event.report"
    version: Literal["000"] = "000"
