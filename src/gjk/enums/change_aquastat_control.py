# Literal Enum:
#  - no additional values can be added over time.
#  - Sent as-is, not in hex symbol
from enum import auto
from typing import List

from gw.enums import GwStrEnum


class ChangeAquastatControl(GwStrEnum):
    """
    A Finite State Machine action changing the function of an Aquastat Control
    """

    SwitchToBoiler = auto()
    SwitchToScada = auto()

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]

    @classmethod
    def default(cls) -> "ChangeAquastatControl":
        return cls.SwitchToBoiler

    @classmethod
    def enum_name(cls) -> str:
        return "change.aquastat.control"
