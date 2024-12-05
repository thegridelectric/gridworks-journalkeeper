"""Type my.channels, version 000"""

from typing import List, Literal

from gw.named_types import GwBase

from gjk.named_types.data_channel_gt import DataChannelGt
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
    UUID4Str,
)


class MyChannels(GwBase):
    from_g_node_alias: LeftRightDot
    from_g_node_instance_id: UUID4Str
    message_created_ms: UTCMilliseconds
    message_id: UUID4Str
    channel_list: List[DataChannelGt]
    type_name: Literal["my.channels"] = "my.channels"
    version: Literal["000"] = "000"
