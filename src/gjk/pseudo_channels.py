# A PseudoChannel is something that:
#   1. We store in the database as a channel
#   2. We store readings for (in the readings table)
#   3. Is not a DataChannel or a DerivedChannel defined in the hardware layout
#
# This includes things like price, weather, ShNode states, etc.
#
# LayoutLitePersistor syncs the registered pseudo-channels with the database.
# Other persistors query the pseudo-channels from the database and store readings for them.

from collections.abc import Callable

from gjk.sema.types import LayoutLite
from gjk.sema.types.old_versions.layout_lite_001 import LayoutLite001
from gjk.sema.types.old_versions.layout_lite_002 import LayoutLite002
from gjk.sema.types.old_versions.layout_lite_003 import LayoutLite003
from gjk.sema.types.old_versions.layout_lite_004 import LayoutLite004
from gjk.sema.types.old_versions.layout_lite_005 import LayoutLite005
from gjk.sema.types.old_versions.layout_lite_006 import LayoutLite006
from gjk.sema.types.old_versions.layout_lite_007 import LayoutLite007
from gjk.sema.types.old_versions.layout_lite_008 import LayoutLite008
from gjk.sema.types.old_versions.layout_lite_009 import LayoutLite009
from gjk.sema.types.old_versions.layout_lite_010 import LayoutLite010
from gjk.sema.types.old_versions.layout_lite_011 import LayoutLite011

# Every layout.lite version JK persists natively, split by channel
# projection: 001-006 are the historical SynthChannels-era versions
# (backfilled from the S3 archive); 007+ carry DerivedChannels instead.
type SynthEraLayout = (
    LayoutLite006
    | LayoutLite005
    | LayoutLite004
    | LayoutLite003
    | LayoutLite002
    | LayoutLite001
)
type DerivedEraLayout = (
    LayoutLite
    | LayoutLite011
    | LayoutLite010
    | LayoutLite009
    | LayoutLite008
    | LayoutLite007
)
type ModernLayout = DerivedEraLayout | SynthEraLayout


class PseudoChannel:
    CHANNEL_TYPE = "gjk.pseudo"

    def __init__(self, name: str, display_name: str, unit, unit_type: str):
        self.name = name
        self.display_name = display_name
        self.unit = unit
        self.unit_type = unit_type


type PseudoChannelFactory = Callable[[ModernLayout], list[PseudoChannel]]
_REGISTERED_CHANNEL_FACTORIES: list[PseudoChannelFactory] = []


def register_pseudo_channel_factory(factory: PseudoChannelFactory):
    _REGISTERED_CHANNEL_FACTORIES.append(factory)


def get_pseudo_channels(layout: ModernLayout):
    for f in _REGISTERED_CHANNEL_FACTORIES:
        yield from f(layout)
