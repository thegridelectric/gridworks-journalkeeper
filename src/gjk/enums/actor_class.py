from enum import auto

from gw.enums import GwStrEnum


class ActorClass(GwStrEnum):
    NoActor = auto()
    PrimaryScada = auto()
    SecondaryScada = auto()
    Scada = auto()
    HomeAlone = auto()
    BooleanActuator = auto()
    PowerMeter = auto()
    LocalControl = auto()
    LeafAlly = auto()
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
    I2cZeroTenMultiplexer = auto()
    ZeroTenOutputer = auto()
    AtomicAlly = auto()
    SynthGenerator = auto()
    FakeAtn = auto()
    PumpDoctor = auto()
    StratBoss = auto()
    HpRelayBoss = auto()
    HpBoss = auto()
    ApiBtuMeter = auto()
    DerivedGenerator = auto()
    SiegLoop = auto()
    GpioSensor = auto()
    I2cBus = auto()
    I2cRelayBoard = auto()
    I2cThermistorReader = auto()

    @classmethod
    def default(cls) -> "ActorClass":
        return cls.NoActor

    @classmethod
    def values(cls) -> list[str]:
        return [elt.value for elt in cls]

    @classmethod
    def enum_name(cls) -> str:
        return "sh.actor.class"

    @classmethod
    def enum_version(cls) -> str:
        return "009"
