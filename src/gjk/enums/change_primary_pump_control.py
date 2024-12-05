
# Literal Enum:
#  - no additional values can be added over time.
#  - Sent as-is, not in hex symbol
from enum import auto
from typing import List

from gw.enums import GwStrEnum


class ChangePrimaryPumpControl(GwStrEnum):
    """
    Change control between the fallback HP control and SCADA
    """

    SwitchToScada = auto()
    SwitchToHeatPump = auto()

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]

    @classmethod
    def default(cls) -> "ChangePrimaryPumpControl":
        return cls.SwitchToHeatPump

    @classmethod
    def enum_name(cls) -> str:
        return "change.primary.pump.control"
