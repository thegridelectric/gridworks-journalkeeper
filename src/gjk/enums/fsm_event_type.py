from enum import auto
from typing import List, Optional

from gw.enums import GwStrEnum


class FsmEventType(GwStrEnum):
    """
    The name of a set of events for a particular Spaceheat finite state machine.

    Enum sh.fsm.event.type version 000 in the GridWorks Type registry.

    Used by multiple Application Shared Languages (ASLs). For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shfsmeventtype)
      - [More Info](https://gridworks-protocol.readthedocs.io/en/latest/finite-state-machines.html)

    Values (with symbols in parens):
      - ChangeRelayPin (a2b691bb): Meant to be used between a single relay actor and a multiplexer
        (for example, an i2c relay actor and an i2c relay multiplexer). The associated values
        are DeEnergized and Energized. Note that the multiplexer does not concern itself with
        the configuration of the relay (NormallyOpen, NormallyClosed, DoubleThrow). Instead,
        it just makes sure it is receiving a ChangeRelayPin command from one of its known relays.
      - ChangeRelayState (00000000): Meant to be used for a relay whose RelayConfig is NormallyOpen
        or NormallyClosed (not DoubleThrow). Associated values are CloseRelay and OpenRelay
        - so it is meant to be a layer up in abstraction from sending energization/de-energization
        commands to the pin. The sender indeed does not need to know whether the relay is normally
        open or normally closed (although obviously the receiver must know).
      - SetAnalog010V (bbef899f)
      - SetAnalog420mA (aa4b0c96)
      - ChangeValveState (c234ee7a)
      - ChangeStoreFlowDirection (1efc9909)
      - ChangeHeatcallSource (c5717e64)
      - ChangeAquastatControl (0066a412)
      - ChangeHeatPumpControl (50ea0661)
      - ChangeLgOperatingMode (89a98375)
      - TimerFinished (9e44ab43)
      - ChangePrimaryPumpState (d71c8c2a)
      - ChangePrimaryPumpControl (7f34907c): Change control of the primary pump between the Heat
        pump and the SCADA
    """

    ChangeRelayPin = auto()
    ChangeRelayState = auto()
    SetAnalog010V = auto()
    SetAnalog420mA = auto()
    ChangeValveState = auto()
    ChangeStoreFlowDirection = auto()
    ChangeHeatcallSource = auto()
    ChangeAquastatControl = auto()
    ChangeHeatPumpControl = auto()
    ChangeLgOperatingMode = auto()
    TimerFinished = auto()
    ChangePrimaryPumpState = auto()
    ChangePrimaryPumpControl = auto()

    @classmethod
    def default(cls) -> "FsmEventType":
        """
        Returns default value (in this case ChangeRelayState)
        """
        return cls.ChangeRelayState

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
        The name in the GridWorks Type Registry (sh.fsm.event.type)
        """
        return "sh.fsm.event.type"

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
            a later version of this enum, returns the default value of "ChangeRelayState".
        """
        if symbol not in symbol_to_value.keys():
            return cls.default().value
        return symbol_to_value[symbol]

    @classmethod
    def value_to_symbol(cls, value: str) -> str:
        """
        Provides the encoding symbol for a FsmEventType enum to send in seriliazed messages.

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
            "a2b691bb",
            "00000000",
            "bbef899f",
            "aa4b0c96",
            "c234ee7a",
            "1efc9909",
            "c5717e64",
            "0066a412",
            "50ea0661",
            "89a98375",
            "9e44ab43",
            "d71c8c2a",
            "7f34907c",
        ]


symbol_to_value = {
    "a2b691bb": "ChangeRelayPin",
    "00000000": "ChangeRelayState",
    "bbef899f": "SetAnalog010V",
    "aa4b0c96": "SetAnalog420mA",
    "c234ee7a": "ChangeValveState",
    "1efc9909": "ChangeStoreFlowDirection",
    "c5717e64": "ChangeHeatcallSource",
    "0066a412": "ChangeAquastatControl",
    "50ea0661": "ChangeHeatPumpControl",
    "89a98375": "ChangeLgOperatingMode",
    "9e44ab43": "TimerFinished",
    "d71c8c2a": "ChangePrimaryPumpState",
    "7f34907c": "ChangePrimaryPumpControl",
}

value_to_symbol = {value: key for key, value in symbol_to_value.items()}

value_to_version = {
    "ChangeRelayPin": "000",
    "ChangeRelayState": "000",
    "SetAnalog010V": "000",
    "SetAnalog420mA": "000",
    "ChangeValveState": "000",
    "ChangeStoreFlowDirection": "000",
    "ChangeHeatcallSource": "000",
    "ChangeAquastatControl": "000",
    "ChangeHeatPumpControl": "000",
    "ChangeLgOperatingMode": "000",
    "TimerFinished": "000",
    "ChangePrimaryPumpState": "000",
    "ChangePrimaryPumpControl": "000",
}
