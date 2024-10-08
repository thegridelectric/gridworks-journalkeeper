"""Type gridworks.event.report, version 000"""

from typing import Literal

from gjk.property_format import (
    UTCMilliseconds,
    UUID4Str,
)
from gjk.types.gw_base import GwBase
from gjk.types.report import Report


class GridworksEventReport(GwBase):
    message_id: UUID4Str
    time_created_ms: UTCMilliseconds
    src: str
    report: Report
    type_name: Literal["gridworks.event.report"] = "gridworks.event.report"
    version: Literal["000"] = "000"
