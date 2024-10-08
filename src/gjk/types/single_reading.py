"""Type single.reading, version 000"""

from typing import Literal

from pydantic import StrictInt

from gjk.property_format import (
    SpaceheatName,
    UTCMilliseconds,
)
from gjk.types.gw_base import GwBase


class SingleReading(GwBase):
    channel_name: SpaceheatName
    value: StrictInt
    scada_read_time_unix_ms: UTCMilliseconds
    type_name: Literal["single.reading"] = "single.reading"
    version: Literal["000"] = "000"
