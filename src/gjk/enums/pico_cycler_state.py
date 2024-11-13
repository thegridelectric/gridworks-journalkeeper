from enum import auto
from typing import List, Optional

from gw.enums import GwStrEnum


class PicoCyclerState(GwStrEnum):
    """
    

    Enum pico.cycler.state version 000 in the GridWorks Type registry.

    Used by multiple Application Shared Languages (ASLs). For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#picocyclerstate)

    Values (with symbols in parens):
      - Dormant (a92b2faf)
      - PicosLive (a0d08717)
      - RelayOpening (38018df2)
      - RelayOpen (e4a9faed)
      - RelayClosing (6d260096)
      - PicosRebooting (79f188b6)
      - AllZombies (79df6fde)
    """

    Dormant = auto()
    PicosLive = auto()
    RelayOpening = auto()
    RelayOpen = auto()
    RelayClosing = auto()
    PicosRebooting = auto()
    AllZombies = auto()

    @classmethod
    def default(cls) -> "PicoCyclerState":
        """
        Returns default value (in this case PicosLive)
        """
        return cls.PicosLive

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
        The name in the GridWorks Type Registry (pico.cycler.state)
        """
        return "pico.cycler.state"

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
            a later version of this enum, returns the default value of "PicosLive".
        """
        if symbol not in symbol_to_value.keys():
            return cls.default().value
        return symbol_to_value[symbol]

    @classmethod
    def value_to_symbol(cls, value: str) -> str:
        """
        Provides the encoding symbol for a PicoCyclerState enum to send in seriliazed messages.

        Args:
            symbol (str): The candidate value.

        Returns:
            str: The symbol encoding that value. If the value is not recognized -
            which could happen if the actor making the message used a later version
            of this enum than the actor decoding the message, returns the default
            symbol of "a0d08717".
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
            "a92b2faf",
            "a0d08717",
            "38018df2",
            "e4a9faed",
            "6d260096",
            "79f188b6",
            "79df6fde",
        ]


symbol_to_value = {
    "a92b2faf": "Dormant",
    "a0d08717": "PicosLive",
    "38018df2": "RelayOpening",
    "e4a9faed": "RelayOpen",
    "6d260096": "RelayClosing",
    "79f188b6": "PicosRebooting",
    "79df6fde": "AllZombies",
}

value_to_symbol = {value: key for key, value in symbol_to_value.items()}

value_to_version = {
    "Dormant": "000",
    "PicosLive": "000",
    "RelayOpening": "000",
    "RelayOpen": "000",
    "RelayClosing": "000",
    "PicosRebooting": "000",
    "AllZombies": "000",
}
