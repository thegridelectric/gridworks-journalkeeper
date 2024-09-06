# Literal Enum:
#  - no additional values can be added over time.
#  - Sent as-is, not in hex symbol
from enum import auto
from typing import List

from gw.enums import GwStrEnum


class StoreFlowDirection(GwStrEnum):
    """
    Used for a double-throw relay that can toggle between a thermal store heating up (flow is
    in the charging direction) or cooling down (flow is in the discharging direction). Events
    in the StoreFlowDirection finite state machine
    """

    ValvedtoDischargeStore = auto()
    ValvesMovingToCharging = auto()
    ValvedtoChargeStore = auto()
    ValvesMovingToDischarging = auto()

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]

    @classmethod
    def default(cls) -> "StoreFlowDirection":
        return cls.ValvedtoDischargeStore

    @classmethod
    def enum_name(cls) -> str:
        return "store.flow.direction"
