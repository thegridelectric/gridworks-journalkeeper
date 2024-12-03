"""
Tests for enum sh.actor.class.003 from the GridWorks Type Registry.
"""

from gjk.enums import ActorClass


def test_actor_class() -> None:
    assert set(ActorClass.values()) == {
        "NoActor",
        "Scada",
        "HomeAlone",
        "BooleanActuator",
        "PowerMeter",
        "Atn",
        "SimpleSensor",
        "MultipurposeSensor",
        "Thermostat",
        "HubitatTelemetryReader",
        "HubitatTankModule",
        "HubitatPoller",
        "I2cRelayMultiplexer",
        "FlowTotalizer",
        "Relay",
        "Admin",
        "Fsm",
        "Parentless",
        "Hubitat",
        "HoneywellThermostat",
        "ApiTankModule",
        "ApiFlowModule",
        "PicoCycler",
        "I2cDfrMultiplexer",
        "ZeroTenOutputer",
    }

    assert ActorClass.default() == ActorClass.NoActor
    assert ActorClass.enum_name() == "sh.actor.class"
    assert ActorClass.enum_version() == "003"

    assert ActorClass.version("NoActor") == "000"
    assert ActorClass.version("Scada") == "000"
    assert ActorClass.version("HomeAlone") == "000"
    assert ActorClass.version("BooleanActuator") == "000"
    assert ActorClass.version("PowerMeter") == "000"
    assert ActorClass.version("Atn") == "000"
    assert ActorClass.version("SimpleSensor") == "000"
    assert ActorClass.version("MultipurposeSensor") == "000"
    assert ActorClass.version("Thermostat") == "000"
    assert ActorClass.version("HubitatTelemetryReader") == "001"
    assert ActorClass.version("HubitatTankModule") == "001"
    assert ActorClass.version("HubitatPoller") == "001"
    assert ActorClass.version("I2cRelayMultiplexer") == "001"
    assert ActorClass.version("FlowTotalizer") == "001"
    assert ActorClass.version("Relay") == "001"
    assert ActorClass.version("Admin") == "001"
    assert ActorClass.version("Fsm") == "001"
    assert ActorClass.version("Parentless") == "001"
    assert ActorClass.version("Hubitat") == "001"
    assert ActorClass.version("HoneywellThermostat") == "001"
    assert ActorClass.version("ApiTankModule") == "002"
    assert ActorClass.version("ApiFlowModule") == "002"
    assert ActorClass.version("PicoCycler") == "002"
    assert ActorClass.version("I2cDfrMultiplexer") == "003"
    assert ActorClass.version("ZeroTenOutputer") == "003"

    for value in ActorClass.values():
        symbol = ActorClass.value_to_symbol(value)
        assert ActorClass.symbol_to_value(symbol) == value
