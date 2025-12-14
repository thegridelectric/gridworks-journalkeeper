# Literal Enum:
#  - no additional values can be added over time.
#  - Sent as-is, not in hex symbol
from enum import auto
from typing import List

from gw.enums import GwStrEnum


class ChangeStoreFlowDirection(GwStrEnum):
    """
    Events that trigger changing StoreFlowDirection finite state machine
    """

    Discharge = auto()
    Charge = auto()

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]

    @classmethod
    def default(cls) -> "ChangeStoreFlowDirection":
        return cls.Discharge

    @classmethod
    def enum_name(cls) -> str:
        return "change.store.flow.direction"
