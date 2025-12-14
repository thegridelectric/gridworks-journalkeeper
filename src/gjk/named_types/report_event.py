"""Type report.event, version 002"""

from typing import Literal

from gw.named_types import GwBase

from gjk.named_types.report import Report
from gjk.property_format import (
    UTCMilliseconds,
    UUID4Str,
)


class ReportEvent(GwBase):
    message_id: UUID4Str
    time_created_ms: UTCMilliseconds
    src: str
    report: Report
    type_name: Literal["report.event"] = "report.event"
    version: Literal["002"] = "002"
