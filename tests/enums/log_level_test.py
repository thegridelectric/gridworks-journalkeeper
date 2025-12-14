"""
Tests for enum log.level.000 from the GridWorks Type Registry.
"""

from gjk.enums import LogLevel


def test_log_level() -> None:
    assert set(LogLevel.values()) == {
        "Critical",
        "Error",
        "Warning",
        "Info",
        "Debug",
        "Trace",
    }

    assert LogLevel.default() == LogLevel.Info
    assert LogLevel.enum_name() == "log.level"
    assert LogLevel.enum_version() == "000"

    assert LogLevel.version("Critical") == "000"
    assert LogLevel.version("Error") == "000"
    assert LogLevel.version("Warning") == "000"
    assert LogLevel.version("Info") == "000"
    assert LogLevel.version("Debug") == "000"
    assert LogLevel.version("Trace") == "000"

    for value in LogLevel.values():
        symbol = LogLevel.value_to_symbol(value)
        assert LogLevel.symbol_to_value(symbol) == value
