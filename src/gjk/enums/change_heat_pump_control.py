# Literal Enum:
#  - no additional values can be added over time.
#  - Sent as-is, not in hex symbol
from enum import auto
from typing import List

from gw.enums import GwStrEnum


class ChangeHeatPumpControl(GwStrEnum):
    """
    Change control between a fallback analog system and SCADA
    """

    SwitchToTankAquastat = auto()
    SwitchToScada = auto()

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]

    @classmethod
    def default(cls) -> "ChangeHeatPumpControl":
        return cls.SwitchToTankAquastat

    @classmethod
    def enum_name(cls) -> str:
        return "change.heat.pump.control"
