from gjk.pseudo_channels import PseudoChannel
from gjk.sema.enums import Gw1Unit


class ZoneHeatCallPseudoChannel(PseudoChannel):
    def __init__(self, name: str):
        super().__init__(
            name,
            display_name="Heat Call",
            unit=Gw1Unit.Unitless,
            unit_type=Gw1Unit.enum_name(),
        )
