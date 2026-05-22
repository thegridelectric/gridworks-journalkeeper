"""
Tests for enum sh.actor.class.005 from the GridWorks Type Registry.
"""

from gjk.enums import ActorClass


def test_actor_class() -> None:
    assert set(ActorClass.values()) == {
        "NoActor",
        "PrimaryScada",
        "SecondaryScada",
        "Scada",
        "HomeAlone",
        "BooleanActuator",
        "PowerMeter",
        "LocalControl",
        "LeafAlly",
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
        "I2cZeroTenMultiplexer",
        "ZeroTenOutputer",
        "AtomicAlly",
        "SynthGenerator",
        "FakeAtn",
        "PumpDoctor",
        "StratBoss",
        "HpRelayBoss",
        "HpBoss",
        "ApiBtuMeter",
        "DerivedGenerator",
        "SiegLoop",
        "GpioSensor",
        "I2cBus",
        "I2cRelayBoard",
        "I2cThermistorReader",
    }

    assert ActorClass.default() == ActorClass.NoActor
    assert ActorClass.enum_name() == "sh.actor.class"
    assert ActorClass.enum_version() == "009"
