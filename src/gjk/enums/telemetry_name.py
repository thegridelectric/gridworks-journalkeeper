from enum import auto
from typing import List, Optional

from gw.enums import GwStrEnum


class TelemetryName(GwStrEnum):
    """
    Specifies the name of sensed data reported by a Spaceheat SCADA

    Enum spaceheat.telemetry.name version 001 in the GridWorks Type registry.

    Used by multiple Application Shared Languages (ASLs). For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheattelemetryname)
      - [More Info](https://gridworks-protocol.readthedocs.io/en/latest/telemetry-name.html)

    Values (with symbols in parens):
      - Unknown (00000000): Default Value - unknown telemetry name.
      - PowerW (af39eec9): Power in Watts.
      - RelayState (5a71d4b3): The Telemetry reading belongs to ['Energized', 'DeEnergized'] (relay.energization.state
        enum).
      - WaterTempCTimes1000 (c89d0ba1): Water temperature, in Degrees Celcius multiplied by 1000.
        Example: 43200 means 43.2 deg Celcius.
      - WaterTempFTimes1000 (793505aa): Water temperature, in Degrees F multiplied by 1000. Example:
        142100 means 142.1 deg Fahrenheit.
      - GpmTimes100 (d70cce28): Gallons Per Minute multiplied by 100. Example: 433 means 4.33 gallons
        per minute.
      - CurrentRmsMicroAmps (ad19e79c): Current measurement in Root Mean Square MicroAmps.
      - GallonsTimes100 (329a68c0): Gallons multipled by 100. This is useful for flow meters that
        report cumulative gallons as their raw output. Example: 55300 means 55.3 gallons.
      - VoltageRmsMilliVolts (bb6fdd59): Voltage in Root Mean Square MilliVolts.
      - MilliWattHours (e0bb014b): Energy in MilliWattHours.
      - FrequencyMicroHz (337b8659): Frequency in MicroHz. Example: 59,965,332 means 59.965332 Hz.
      - AirTempCTimes1000 (0f627faa): Air temperature, in Degrees Celsius multiplied by 1000. Example:
        6234 means 6.234 deg Celcius.
      - AirTempFTimes1000 (4c3f8c78): Air temperature, in Degrees F multiplied by 1000. Example:
        69329 means 69.329 deg Fahrenheit.
      - ThermostatState (00002000): Thermostat State: 0 means idle, 1 means heating, 2 means pending
        heat
    """

    Unknown = auto()
    PowerW = auto()
    RelayState = auto()
    WaterTempCTimes1000 = auto()
    WaterTempFTimes1000 = auto()
    GpmTimes100 = auto()
    CurrentRmsMicroAmps = auto()
    GallonsTimes100 = auto()
    VoltageRmsMilliVolts = auto()
    MilliWattHours = auto()
    FrequencyMicroHz = auto()
    AirTempCTimes1000 = auto()
    AirTempFTimes1000 = auto()
    ThermostatState = auto()

    @classmethod
    def default(cls) -> "TelemetryName":
        """
        Returns default value (in this case Unknown)
        """
        return cls.Unknown

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
            return "001"
        if not isinstance(value, str):
            raise ValueError("This method applies to strings, not enums")
        if value not in value_to_version.keys():
            raise ValueError(f"Unknown enum value: {value}")
        return value_to_version[value]

    @classmethod
    def enum_name(cls) -> str:
        """
        The name in the GridWorks Type Registry (spaceheat.telemetry.name)
        """
        return "spaceheat.telemetry.name"

    @classmethod
    def enum_version(cls) -> str:
        """
        The version in the GridWorks Type Registry (001)
        """
        return "001"

    @classmethod
    def symbol_to_value(cls, symbol: str) -> str:
        """
        Given the symbol sent in a serialized message, returns the encoded enum.

        Args:
            symbol (str): The candidate symbol.

        Returns:
            str: The encoded value associated to that symbol. If the symbol is not
            recognized - which could happen if the actor making the symbol is using
            a later version of this enum, returns the default value of "Unknown".
        """
        if symbol not in symbol_to_value.keys():
            return cls.default().value
        return symbol_to_value[symbol]

    @classmethod
    def value_to_symbol(cls, value: str) -> str:
        """
        Provides the encoding symbol for a TelemetryName enum to send in seriliazed messages.

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
            "af39eec9",
            "5a71d4b3",
            "c89d0ba1",
            "793505aa",
            "d70cce28",
            "ad19e79c",
            "329a68c0",
            "bb6fdd59",
            "e0bb014b",
            "337b8659",
            "0f627faa",
            "4c3f8c78",
            "00002000",
        ]


symbol_to_value = {
    "00000000": "Unknown",
    "af39eec9": "PowerW",
    "5a71d4b3": "RelayState",
    "c89d0ba1": "WaterTempCTimes1000",
    "793505aa": "WaterTempFTimes1000",
    "d70cce28": "GpmTimes100",
    "ad19e79c": "CurrentRmsMicroAmps",
    "329a68c0": "GallonsTimes100",
    "bb6fdd59": "VoltageRmsMilliVolts",
    "e0bb014b": "MilliWattHours",
    "337b8659": "FrequencyMicroHz",
    "0f627faa": "AirTempCTimes1000",
    "4c3f8c78": "AirTempFTimes1000",
    "00002000": "ThermostatState",
}

value_to_symbol = {value: key for key, value in symbol_to_value.items()}

value_to_version = {
    "Unknown": "000",
    "PowerW": "000",
    "RelayState": "000",
    "WaterTempCTimes1000": "000",
    "WaterTempFTimes1000": "000",
    "GpmTimes100": "000",
    "CurrentRmsMicroAmps": "000",
    "GallonsTimes100": "000",
    "VoltageRmsMilliVolts": "001",
    "MilliWattHours": "001",
    "FrequencyMicroHz": "001",
    "AirTempCTimes1000": "001",
    "AirTempFTimes1000": "001",
    "ThermostatState": "001",
}
