"""Type layout.event, version 000"""

from typing import Literal

from gw.named_types import GwBase

from gjk.named_types.layout_lite import LayoutLite
from gjk.property_format import (
    UTCMilliseconds,
    UUID4Str,
)


class LayoutEvent(GwBase):
    message_id: UUID4Str
    time_created_ms: UTCMilliseconds
    src: str
    layout: LayoutLite
    type_name: Literal["layout.event"] = "layout.event"
    version: Literal["000"] = "000"
