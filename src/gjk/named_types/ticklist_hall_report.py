from typing import Literal

from gw.named_types import GwBase

from gjk.named_types.ticklist_hall import TicklistHall
from gjk.property_format import LeftRightDot, SpaceheatName, UTCMilliseconds


class TicklistHallReport(GwBase):
    terminal_asset_alias: LeftRightDot
    actor_node_name: SpaceheatName
    scada_received_unix_ms: UTCMilliseconds
    tick_list: TicklistHall
    type_name: Literal["ticklist.hall.report"] = "ticklist.hall.report"
    version: Literal["000"] = "000"