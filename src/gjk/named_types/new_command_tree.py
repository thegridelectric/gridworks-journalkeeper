"""Type new.command.tree, version 000"""

from typing import List, Literal

from gw.named_types import GwBase

from gjk.named_types.spaceheat_node_gt import SpaceheatNodeGt
from gjk.property_format import (
    LeftRightDot,
    UTCMilliseconds,
)


class NewCommandTree(GwBase):
    from_g_node_alias: LeftRightDot
    sh_nodes: List[SpaceheatNodeGt]
    unix_ms: UTCMilliseconds
    type_name: Literal["new.command.tree"] = "new.command.tree"
    version: Literal["000"] = "000"
