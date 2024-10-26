from typing import Literal

from gw.named_types import GwBase

from gjk.named_types.ticklist_reed import TicklistReed
from gjk.property_format import LeftRightDot, SpaceheatName, UTCMilliseconds


class TicklistReedReport(GwBase):
    terminal_asset_alias: LeftRightDot
    actor_node_name: SpaceheatName
    scada_received_unix_ms: UTCMilliseconds
    ticklist: TicklistReed
    type_name: Literal["ticklist.reed.report"] = "ticklist.reed.report"
    version: Literal["000"] = "000"
