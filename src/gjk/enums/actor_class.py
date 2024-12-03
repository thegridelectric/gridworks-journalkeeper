from enum import auto
from typing import List, Optional

from gw.enums import GwStrEnum


class ActorClass(GwStrEnum):
    """
    Determines the code running Spaceheat Nodes supervised by Spaceheat SCADA software

    Enum sh.actor.class version 003 in the GridWorks Type registry.

    Used by multiple Application Shared Languages (ASLs). For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shactorclass)
      - [More Info](https://gridworks-protocol.readthedocs.io/en/latest/actor-class.html)

    Values (with symbols in parens):
      - NoActor (00000000): A SpaceheatNode that does not have any code running on its behalf within
        the SCADA, but is instead only a reference object (for example, a tank of hot water
        or a resistive element) that can be discussed (for example, the power drawn by the resistive
        element can be measured) or evaluated (for example, a set of 5 different temperatures
        in different places on the tank can be used to estimate total thermal energy in the
        tank).
      - Scada (6d37aa41): The SCADA actor is the prime piece of code running and supervising other
        ProActors within the SCADA code. It is also responsible for managing the state of TalkingWith
        the AtomicTNode, as well maintaining and reporting a boolean state variable that indicates
        whether it is following dispatch commands from the AtomicTNode XOR following dispatch
        commands from its own HomeAlone actor.
      - HomeAlone (32d3d19f): HomeAlone is an abstract Spaceheat Actor responsible for dispatching
        the SCADA when it is not talking with the AtomicTNode.
      - BooleanActuator (fddd0064): A SpaceheatNode representing a generic boolean actuator capable
        of turning on (closing a circuit) or turning off (opening a circuit). If the device
        is a relay that can be directly energized or de-energized, recommend using Relay actor
        instead.
      - PowerMeter (2ea112b9): A SpaceheatNode representing the power meter that is used to settle
        financial transactions with the TerminalAsset. That is, this is the power meter whose
        accuracy is certified in the creation of the TerminalAsset GNode via creation of the
        TaDeed. [More Info](https://gridworks.readthedocs.io/en/latest/terminal-asset.html).
      - Atn (b103058f): A SpaceheatNode representing the AtomicTNode. Note that the code running
        the AtomicTNode is not local within the SCADA code, except for a stub used for testing
        purposes. [More Info](https://gridworks.readthedocs.io/en/latest/atomic-t-node.html).
      - SimpleSensor (dae4b2f0): A SpaceheatNode representing a sensor that measures a single category
        of quantity (for example, temperature) for a single object (for example, on a pipe). [More Info](https://gridworks-protocol.readthedocs.io/en/latest/simple-sensor.html).
      - MultipurposeSensor (7c483ad0): A sensor that either reads multiple kinds of readings from
        the same sensing device (for example reads current and voltage), reads multiple different
        objects (temperature from two different thermisters) or both. [More Info](https://gridworks-protocol.readthedocs.io/en/latest/multipurpose-sensor.html).
      - Thermostat (4a9c1785): A SpaceheatNode representing a thermostat.
      - HubitatTelemetryReader (0401b27e): A generic actor for reading telemetry data from a Hubitat
        Home Automation Hub LAN API. [More Info](https://drive.google.com/drive/u/0/folders/1AqAU_lC2phzuI9XRYvogiIYA7GXNtlr6).
      - HubitatTankModule (e2877329): The actor for running a GridWorks TankModule, comprised of
        two Z-Wave Fibaro temp sensors built together inside a small container that has 4 thermistors
        attached. These are designed to be installed from top (1) to bottom (4) on a stratified
        thermal storage tank. [More Info](https://drive.google.com/drive/u/0/folders/1GSxDd8Naf1GKK_fSOgQU933M1UcJ4r8q).
      - HubitatPoller (00000100): An actor for representing a somewhat generic ShNode (like a thermostat)
        that can be polled through the Hubitat.
      - I2cRelayMultiplexer (cdf7df88): Responsible for maintaining a single i2c bus object
      - FlowTotalizer (06b306e7): Attached to a driver that reads liquid flow by counting pulses
        from a flow meter that creates pulses and integrating the result (known as a totalizer
        in the industry).
      - Relay (49951f59): An actor representing a relay. If the device is indeed relay that can be
        directly energized or de-energized, recommend using Relay instead of BooleanActuator
      - Admin (4d5f791b): Actor for taking control of all of the actuators - flattening the hierarchy
        and disabling all finite state machines.
      - Fsm (2abcea3d): Actor Class for Finite State Machine actors. For these actors, the code is
        determined by the ShNode Name instead of just the ActorClass.
      - Parentless (65136bd8): An actor that has no parent and is also not the primary SCADA. Used
        when there are multiple devices in the SCADA's system. For example, two Pis - one running
        the primary SCADA code and temp sensors, the other running relays and 0-10V output devices.
        A Parentless actor on the second Pi is responsible for spinning up the relay- and 0-10V
        output actors.
      - Hubitat (00000101): An actor for representing a Hubitat for receiving Hubitat events over
        HTTP.
      - HoneywellThermostat (00000102): An actor for representing a Honeywell Hubitat thermostat
        which can load thermostat heating state change messages into status reports.
      - ApiTankModule (92b7d814)
      - ApiFlowModule (29939d30)
      - PicoCycler (99aa2b9b)
      - I2cDfrMultiplexer (adb77b99)
      - ZeroTenOutputer (2807d1af)
    """

    NoActor = auto()
    Scada = auto()
    HomeAlone = auto()
    BooleanActuator = auto()
    PowerMeter = auto()
    Atn = auto()
    SimpleSensor = auto()
    MultipurposeSensor = auto()
    Thermostat = auto()
    HubitatTelemetryReader = auto()
    HubitatTankModule = auto()
    HubitatPoller = auto()
    I2cRelayMultiplexer = auto()
    FlowTotalizer = auto()
    Relay = auto()
    Admin = auto()
    Fsm = auto()
    Parentless = auto()
    Hubitat = auto()
    HoneywellThermostat = auto()
    ApiTankModule = auto()
    ApiFlowModule = auto()
    PicoCycler = auto()
    I2cDfrMultiplexer = auto()
    ZeroTenOutputer = auto()

    @classmethod
    def default(cls) -> "ActorClass":
        """
        Returns default value (in this case NoActor)
        """
        return cls.NoActor

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
            return "003"
        if not isinstance(value, str):
            raise ValueError("This method applies to strings, not enums")
        if value not in value_to_version.keys():
            raise ValueError(f"Unknown enum value: {value}")
        return value_to_version[value]

    @classmethod
    def enum_name(cls) -> str:
        """
        The name in the GridWorks Type Registry (sh.actor.class)
        """
        return "sh.actor.class"

    @classmethod
    def enum_version(cls) -> str:
        """
        The version in the GridWorks Type Registry (003)
        """
        return "003"

    @classmethod
    def symbol_to_value(cls, symbol: str) -> str:
        """
        Given the symbol sent in a serialized message, returns the encoded enum.

        Args:
            symbol (str): The candidate symbol.

        Returns:
            str: The encoded value associated to that symbol. If the symbol is not
            recognized - which could happen if the actor making the symbol is using
            a later version of this enum, returns the default value of "NoActor".
        """
        if symbol not in symbol_to_value.keys():
            return cls.default().value
        return symbol_to_value[symbol]

    @classmethod
    def value_to_symbol(cls, value: str) -> str:
        """
        Provides the encoding symbol for a ActorClass enum to send in seriliazed messages.

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
            "6d37aa41",
            "32d3d19f",
            "fddd0064",
            "2ea112b9",
            "b103058f",
            "dae4b2f0",
            "7c483ad0",
            "4a9c1785",
            "0401b27e",
            "e2877329",
            "00000100",
            "cdf7df88",
            "06b306e7",
            "49951f59",
            "4d5f791b",
            "2abcea3d",
            "65136bd8",
            "00000101",
            "00000102",
            "92b7d814",
            "29939d30",
            "99aa2b9b",
            "adb77b99",
            "2807d1af",
        ]


symbol_to_value = {
    "00000000": "NoActor",
    "6d37aa41": "Scada",
    "32d3d19f": "HomeAlone",
    "fddd0064": "BooleanActuator",
    "2ea112b9": "PowerMeter",
    "b103058f": "Atn",
    "dae4b2f0": "SimpleSensor",
    "7c483ad0": "MultipurposeSensor",
    "4a9c1785": "Thermostat",
    "0401b27e": "HubitatTelemetryReader",
    "e2877329": "HubitatTankModule",
    "00000100": "HubitatPoller",
    "cdf7df88": "I2cRelayMultiplexer",
    "06b306e7": "FlowTotalizer",
    "49951f59": "Relay",
    "4d5f791b": "Admin",
    "2abcea3d": "Fsm",
    "65136bd8": "Parentless",
    "00000101": "Hubitat",
    "00000102": "HoneywellThermostat",
    "92b7d814": "ApiTankModule",
    "29939d30": "ApiFlowModule",
    "99aa2b9b": "PicoCycler",
    "adb77b99": "I2cDfrMultiplexer",
    "2807d1af": "ZeroTenOutputer",
}

value_to_symbol = {value: key for key, value in symbol_to_value.items()}

value_to_version = {
    "NoActor": "000",
    "Scada": "000",
    "HomeAlone": "000",
    "BooleanActuator": "000",
    "PowerMeter": "000",
    "Atn": "000",
    "SimpleSensor": "000",
    "MultipurposeSensor": "000",
    "Thermostat": "000",
    "HubitatTelemetryReader": "001",
    "HubitatTankModule": "001",
    "HubitatPoller": "001",
    "I2cRelayMultiplexer": "001",
    "FlowTotalizer": "001",
    "Relay": "001",
    "Admin": "001",
    "Fsm": "001",
    "Parentless": "001",
    "Hubitat": "001",
    "HoneywellThermostat": "001",
    "ApiTankModule": "002",
    "ApiFlowModule": "002",
    "PicoCycler": "002",
    "I2cDfrMultiplexer": "003",
    "ZeroTenOutputer": "003",
}
