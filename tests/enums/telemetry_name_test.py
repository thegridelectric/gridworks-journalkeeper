"""
Tests for enum spaceheat.telemetry.name.001 from the GridWorks Type Registry.
"""

from gjk.enums import TelemetryName


def test_telemetry_name() -> None:
    assert set(TelemetryName.values()) == {
        "Unknown",
        "PowerW",
        "RelayState",
        "WaterTempCTimes1000",
        "WaterTempFTimes1000",
        "GpmTimes100",
        "CurrentRmsMicroAmps",
        "GallonsTimes100",
        "VoltageRmsMilliVolts",
        "MilliWattHours",
        "MicroHz",
        "AirTempCTimes1000",
        "AirTempFTimes1000",
        "ThermostatState",
        "MicroVolts",
    }

    assert TelemetryName.default() == TelemetryName.Unknown
    assert TelemetryName.enum_name() == "spaceheat.telemetry.name"
    assert TelemetryName.enum_version() == "001"

    assert TelemetryName.version("Unknown") == "000"
    assert TelemetryName.version("PowerW") == "000"
    assert TelemetryName.version("RelayState") == "000"
    assert TelemetryName.version("WaterTempCTimes1000") == "000"
    assert TelemetryName.version("WaterTempFTimes1000") == "000"
    assert TelemetryName.version("GpmTimes100") == "000"
    assert TelemetryName.version("CurrentRmsMicroAmps") == "000"
    assert TelemetryName.version("GallonsTimes100") == "000"
    assert TelemetryName.version("VoltageRmsMilliVolts") == "001"
    assert TelemetryName.version("MilliWattHours") == "001"
    assert TelemetryName.version("MicroHz") == "001"
    assert TelemetryName.version("AirTempCTimes1000") == "001"
    assert TelemetryName.version("AirTempFTimes1000") == "001"
    assert TelemetryName.version("ThermostatState") == "001"
    assert TelemetryName.version("MicroVolts") == "001"

    for value in TelemetryName.values():
        symbol = TelemetryName.value_to_symbol(value)
        assert TelemetryName.symbol_to_value(symbol) == value
