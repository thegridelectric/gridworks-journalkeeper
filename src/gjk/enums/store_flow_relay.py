from enum import auto
from typing import List, Optional

from gw.enums import GwStrEnum


class StoreFlowRelay(GwStrEnum):
    """
    Used for a double-throw relay that can toggle between a thermal store heating up (flow is
    in the charging direction) or cooling down (flow is in the discharging direction). Events
    in the StoreFlowDirection finite state machine

    Enum store.flow.relay version 000 in the GridWorks Type registry.

    Used by multiple Application Shared Languages (ASLs). For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#storeflowrelay)

    Values (with symbols in parens):
      - DischargingStore (00000000): Thermal store is discharging (and heating the building)
      - ChargingStore (00b3ec5e): Thermal store is charging from an external source (like a heat
        pump or oil boiler).
    """

    DischargingStore = auto()
    ChargingStore = auto()

    @classmethod
    def default(cls) -> "StoreFlowRelay":
        """
        Returns default value (in this case DischargingStore)
        """
        return cls.DischargingStore

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]

    @classmethod
    def version(cls, value: Optional[str] = None) -> str:
        """
        Returns the version of the class (default) used by this package or the
        version of a candidate enum value (always less than or equal to the version
        of the class)

        Args:
            value (Optional[str]): None (for version of the Enum itself) or
            the candidate enum value.

        Raises:
            ValueError: If the value is not one of the enum values.

        Returns:
            str: The version of the enum used by this code (if given no
            value) OR the earliest version of the enum containing the value.
        """
        if value is None:
            return "000"
        if not isinstance(value, str):
            raise ValueError("This method applies to strings, not enums")
        if value not in value_to_version.keys():
            raise ValueError(f"Unknown enum value: {value}")
        return value_to_version[value]

    @classmethod
    def enum_name(cls) -> str:
        """
        The name in the GridWorks Type Registry (store.flow.relay)
        """
        return "store.flow.relay"

    @classmethod
    def enum_version(cls) -> str:
        """
        The version in the GridWorks Type Registry (000)
        """
        return "000"

    @classmethod
    def symbol_to_value(cls, symbol: str) -> str:
        """
        Given the symbol sent in a serialized message, returns the encoded enum.

        Args:
            symbol (str): The candidate symbol.

        Returns:
            str: The encoded value associated to that symbol. If the symbol is not
            recognized - which could happen if the actor making the symbol is using
            a later version of this enum, returns the default value of "DischargingStore".
        """
        if symbol not in symbol_to_value.keys():
            return cls.default().value
        return symbol_to_value[symbol]

    @classmethod
    def value_to_symbol(cls, value: str) -> str:
        """
        Provides the encoding symbol for a StoreFlowRelay enum to send in seriliazed messages.

        Args:
            symbol (str): The candidate value.

        Returns:
            str: The symbol encoding that value. If the value is not recognized -
            which could happen if the actor making the message used a later version
            of this enum than the actor decoding the message, returns the default
            symbol of "00000000".
        """
        if value not in value_to_symbol.keys():
            return value_to_symbol[cls.default().value]
        return value_to_symbol[value]

    @classmethod
    def symbols(cls) -> List[str]:
        """
        Returns a list of the enum symbols
        """
        return [
            "00000000",
            "00b3ec5e",
        ]


symbol_to_value = {
    "00000000": "DischargingStore",
    "00b3ec5e": "ChargingStore",
}

value_to_symbol = {value: key for key, value in symbol_to_value.items()}

value_to_version = {
    "DischargingStore": "000",
    "ChargingStore": "000",
}
