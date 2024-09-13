# Literal Enum:
#  - no additional values can be added over time.
#  - Sent as-is, not in hex symbol
from enum import auto
from typing import List

from gw.enums import GwStrEnum


class ChangeLgOperatingMode(GwStrEnum):
    """
    Clarifies the request and the action in changing between lg.operating.modes
    """

    SwitchToDhw = auto()
    SwitchToHeat = auto()

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]

    @classmethod
    def default(cls) -> "ChangeLgOperatingMode":
        return cls.SwitchToHeat

    @classmethod
    def enum_name(cls) -> str:
        return "change.lg.operating.mode"
