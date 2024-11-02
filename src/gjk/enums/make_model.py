from enum import auto
from typing import List, Optional

from gw.enums import GwStrEnum


class MakeModel(GwStrEnum):
    """
    Determines Make/Model of device associated to a Spaceheat Node supervised by SCADA

    Enum spaceheat.make.model version 003 in the GridWorks Type registry.

    Used by multiple Application Shared Languages (ASLs). For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheatmakemodel)
      - [More Info](https://gridworks-protocol.readthedocs.io/en/latest/make-model.html)

    Values (with symbols in parens):
      - UnknownMake__UnknownModel (00000000)
      - Egauge__4030 (beb6d3fb): A power meter in Egauge's 403x line. [More Info](https://drive.google.com/drive/u/0/folders/1abJ-o9tlTscsQpMvT6SHxIm5j5aODgfA).
      - NCD__PR8-14-SPST (fabfa505): NCD's 4-channel high-power relay controller + 4 GPIO with I2C
        interface. [More Info](https://store.ncd.io/product/4-channel-high-power-relay-controller-4-gpio-with-i2c-interface/?attribute_pa_choose-a-relay=20-amp-spdt).
      - Adafruit__642 (acd93fb3): Adafruit's high-temp, water-proof 1-wire temp sensor. [More Info](https://www.adafruit.com/product/642).
      - GridWorks__TSnap1 (d0178dc3): Actual GridWorks TSnap 1.0 SCADA Box.
      - GridWorks__WaterTempHighPrecision (f8b497e8): PlaceHolder for some new GridWorks designed
        device.
      - Gridworks__SimPm1 (076da322): Simulated power meter.
      - SchneiderElectric__Iem3455 (d300635e): Schneider Electric IEM 344 utility meter.
      - GridWorks__SimBool30AmpRelay (e81d74a8): Simulated relay.
      - OpenEnergy__EmonPi (c75d269f): Open Energy's open source multipurpose sensing device (including
        internal power meter). [More Info](https://docs.openenergymonitor.org/emonpi/technical.html).
      - GridWorks__SimTSnap1 (3042c432): Simulated SCADA Box.
      - Atlas__EzFlo (d0b0e375): Atlas Scientific EZO Embedded Flow Meter Totalizer, pulse to I2C. [More Info](https://drive.google.com/drive/u/0/folders/142bBV1pQIbMpyIR_0iRUr5gnzWgknOJp).
      - Hubitat__C7__LAN1 (4d649420): This refers to a Hubitat C7 that has been configured in a specific
        way with respect to the APIs it presents on the Local Area Network. The Hubitat C7 is
        a home automation hub that supports building ZigBee and ZWave meshes, plugs into Ethernet,
        has a reasonable user interface and has an active community of open-source developers
        who create drivers and package managers for devices, and supports the creation of various
        types of APIs on the Local Area Network. [More Info](https://drive.google.com/drive/folders/1AqAU_lC2phzuI9XRYvogiIYA7GXNtlr6).
      - GridWorks__Tank_Module_1 (bd759051): This refers to a small module designed and assembled
        by GridWorks that is meant to be mounted to the side of a hot water tank. It requires
        24V DC and has 4 temperature sensors coming out of it labeled 1, 2, 3 and 4. It is meant
        to provide temperature readings (taken within a half a second of each other) of all
        4 of its sensors once a minute. [More Info](https://drive.google.com/drive/folders/1GSxDd8Naf1GKK_fSOgQU933M1UcJ4r8q).
      - Fibaro__Analog_Temp_Sensor (1f19839d): This enum refers to a Fibaro FGBS-222 home automation
        device that has been configured in a specific way. This includes (1) being attached
        to two 10K NTC thermistors and a specific voltage divider circuit that specifies its
        temperature as a function of voltage and (2) one of its potential free outputs being
        in-line with the power of a partner Fibaro, so that it can power cycle its partner (because
        there are reports of Fibaros no longer reporting temp change after weeks or months until
        power cylced). The Fibaro itself is a tiny (29 X 18 X 13 mm) Z-Wave device powered on
        9-30V DC that can read up to 6 1-wire DS18B20 temp sensors, 2 0-10V analog inputs and
        also has 2 potential free outputs. [More Info](https://drive.google.com/drive/u/0/folders/1Muhsvw00goppHIfGSEmreX4hM6V78b-m).
      - Amphenol__NTC_10K_Thermistor_MA100GG103BN (46f21cd5): A small gauge, low-cost, rapid response
        NTC 10K Thermistor designed for medical applications. [More Info](https://drive.google.com/drive/u/0/folders/11HW4ov66UvxKAwqApW6IrtoXatZBLQkd).
      - YHDC__SCT013-100 (08da3f7d): YHDC current transformer. [More Info](https://en.yhdc.com/product/SCT013-401.html).
      - Magnelab__SCT-0300-050 (a8d9a70d): Magnelab 50A current transformer.
      - GridWorks__MultiTemp1 (bb31d136): GridWorks ADS 1115-based analog temperature sensor that
        has 12 channels (labeled 1-12) to read 12 10K NTC Thermistors. It is comprised of 3
        NCD ADS 1115 I2C temperature sensors with I2C Addresses 0x4b, 0x48, 0x49. [More Info](https://drive.google.com/drive/u/0/folders/1OuY0tunaad2Ie4Id3zFB7FcbEwHizWuL).
      - Krida__Emr16-I2c-V3 (3353ce46): 16-Channel I2C Low Voltage Electromagnetic Relay Board. [More Info](https://drive.google.com/drive/u/0/folders/1jL82MTRKEh9DDmxJFQ2yU2cjqnVD9Ik7).
      - Omega__FTB8007HW-PT (5bd81968): A double-jet reed pulse producing Flow Meter with 3/4" pipe,
        one pulse per 1/10th of a gallon. [More Info](https://drive.google.com/drive/u/0/folders/1gPR4nIGUuEVyBqBjb2wfY1Znqh6MvKWw).
      - Istec_4440 (99d961da): A double-jet reed pulse producing Flow Meter with 3/4" pipe, somewhat
        strange pulse output. [More Info](https://drive.google.com/drive/u/0/folders/1nioNO_XeEzE4NQJKXvuFq74_HH1vwRc6).
      - Omega__FTB8010HW-PT (39f97379): A double-jet reed pulse producingFlow Meter with 1" pipe,
        one pulse per gallon. Rated for water to 195F. [More Info](https://drive.google.com/drive/u/0/folders/1fiFr9hwYGeXZ1SmpxaSz_XROhfThGbq8).
      - Belimo__BallValve232VS (71a58010): Belimo Ball Valve. Configurable to be either normally
        open or normally closed. Goes into its powered position over about a minute and winds
        up a spring as it does that. Moves back to un-powered position in about 20 seconds, [More Info](https://drive.google.com/drive/u/0/folders/1eTqPNKaKzjKSWwnvY36tZkkv4WVdvrR3).
      - Belimo__DiverterB332L (a156568f): Belimo 3-way diverter valve, 1.25", 24 VAC, spring return
        actuator. [More Info](https://drive.google.com/drive/u/0/folders/1YF_JdUoXrT3bDoXvEwqEvAi7EjahErHk).
      - Taco__0034ePLUS (94efd0b3): Taco 0034ePLUS 010V controllable pump. [More Info](https://drive.google.com/drive/u/0/folders/1GUaQnrfiJeAmmfMiZT1fjPPIXxcTtTsj).
      - Taco__007e (88e512cb): Taco 007e basic circulator pump. [More Info](https://drive.google.com/drive/u/0/folders/12LIMxHMFXujV7mY53IItKP3J2EaM2JlV).
      - Armstrong__CompassH (22a3fc2a): Armstrong CompassH 010V controllable pump. [More Info](https://drive.google.com/drive/u/0/folders/1lpdvjVYD9qk7AHQnRSoY9Xf_o_L0tY38).
      - Honeywell__T6-ZWave-Thermostat (d86abb96): Honeywell TH6320ZW2003 T6 Pro Series Z-Wave Thermostat. [More Info](https://drive.google.com/drive/u/0/folders/1mqnU95tOdeeSGA6o3Ac_sJ1juDy84BIE).
      - PRMFiltration__WM075 (6a9541d9): A double-jet reed pulse producing Flow Meter with 3/4" pipe,
        one pulse per gallon. Cheaper than omegas. [More Info](https://drive.google.com/drive/u/0/folders/1LW-8GHekH9I8vUtT7_xC_9KvkwfZBvid).
      - BellGossett__Ecocirc20_18 (e35655d0): A 0-10V controllable pump that switches out of 0-10V
        control when sent a 0 V signal.
      - Tewa__TT0P-10KC3-T105-1500 (652abfd6): A 10K NTC thermistor used for wrapping around water
        pipes. [More Info](https://drive.google.com/drive/u/0/folders/1lZFZbpjBFgAQ_wlnKJxmEeiN-EOV9Erl).
      - EKM__HOT-SPWM-075-HD (208f827f): 3/4" horizontal hot water flow pulse meter, 1 pulse per
        1/100 cubic ft (~0.0748 gallons).
      - GridWorks__SimMultiTemp (b3eced0d): Simulated 12-channel Ads111x-based analog temp sensor
      - GridWorks__SimTotalizer (e4807056): Simulated I2c-based pulse counter.
      - Krida__Double-Emr16-I2c-V3 (ff529d69): Two 16-Channel I2C Low Voltage Electromagnetic Relay
        Board, with first at address 0x20 and second at address 0x21
      - GridWorks__SimDouble16PinI2cRelay (81d8b222): Simulated I2c Relay board with two boards and
        32 pins (for dev code using Krida__Doubler-Emr16-I2c-V3).
      - GridWorks__TankModule2 (d2d5023f)
      - GridWorks__PicoFlowHall (7d837129)
      - GridWorks__PicoFlowReed (5b11f334)
      - Saier__Sen-HZG1WA (6cb4de48)
    """

    UNKNOWNMAKE__UNKNOWNMODEL = auto()
    EGAUGE__4030 = auto()
    NCD__PR814SPST = auto()
    ADAFRUIT__642 = auto()
    GRIDWORKS__TSNAP1 = auto()
    GRIDWORKS__WATERTEMPHIGHPRECISION = auto()
    GRIDWORKS__SIMPM1 = auto()
    SCHNEIDERELECTRIC__IEM3455 = auto()
    GRIDWORKS__SIMBOOL30AMPRELAY = auto()
    OPENENERGY__EMONPI = auto()
    GRIDWORKS__SIMTSNAP1 = auto()
    ATLAS__EZFLO = auto()
    HUBITAT__C7__LAN1 = auto()
    GRIDWORKS__TANK_MODULE_1 = auto()
    FIBARO__ANALOG_TEMP_SENSOR = auto()
    AMPHENOL__NTC_10K_THERMISTOR_MA100GG103BN = auto()
    YHDC__SCT013100 = auto()
    MAGNELAB__SCT0300050 = auto()
    GRIDWORKS__MULTITEMP1 = auto()
    KRIDA__EMR16I2CV3 = auto()
    OMEGA__FTB8007HWPT = auto()
    ISTEC_4440 = auto()
    OMEGA__FTB8010HWPT = auto()
    BELIMO__BALLVALVE232VS = auto()
    BELIMO__DIVERTERB332L = auto()
    TACO__0034EPLUS = auto()
    TACO__007E = auto()
    ARMSTRONG__COMPASSH = auto()
    HONEYWELL__T6ZWAVETHERMOSTAT = auto()
    PRMFILTRATION__WM075 = auto()
    BELLGOSSETT__ECOCIRC20_18 = auto()
    TEWA__TT0P10KC3T1051500 = auto()
    EKM__HOTSPWM075HD = auto()
    GRIDWORKS__SIMMULTITEMP = auto()
    GRIDWORKS__SIMTOTALIZER = auto()
    KRIDA__DOUBLEEMR16I2CV3 = auto()
    GRIDWORKS__SIMDOUBLE16PINI2CRELAY = auto()
    GRIDWORKS__TANKMODULE2 = auto()
    GRIDWORKS__PICOFLOWHALL = auto()
    GRIDWORKS__PICOFLOWREED = auto()
    SAIER__SENHZG1WA = auto()

    @classmethod
    def default(cls) -> "MakeModel":
        """
        Returns default value (in this case UNKNOWNMAKE__UNKNOWNMODEL)
        """
        return cls.UNKNOWNMAKE__UNKNOWNMODEL

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
        The name in the GridWorks Type Registry (spaceheat.make.model)
        """
        return "spaceheat.make.model"

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
            a later version of this enum, returns the default value of "UnknownMake__UnknownModel".
        """
        if symbol not in symbol_to_value.keys():
            return cls.default().value
        return symbol_to_value[symbol]

    @classmethod
    def value_to_symbol(cls, value: str) -> str:
        """
        Provides the encoding symbol for a MakeModel enum to send in seriliazed messages.

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
            "beb6d3fb",
            "fabfa505",
            "acd93fb3",
            "d0178dc3",
            "f8b497e8",
            "076da322",
            "d300635e",
            "e81d74a8",
            "c75d269f",
            "3042c432",
            "d0b0e375",
            "4d649420",
            "bd759051",
            "1f19839d",
            "46f21cd5",
            "08da3f7d",
            "a8d9a70d",
            "bb31d136",
            "3353ce46",
            "5bd81968",
            "99d961da",
            "39f97379",
            "71a58010",
            "a156568f",
            "94efd0b3",
            "88e512cb",
            "22a3fc2a",
            "d86abb96",
            "6a9541d9",
            "e35655d0",
            "652abfd6",
            "208f827f",
            "b3eced0d",
            "e4807056",
            "ff529d69",
            "81d8b222",
            "d2d5023f",
            "7d837129",
            "5b11f334",
            "6cb4de48",
        ]


symbol_to_value = {
    "00000000": "UNKNOWNMAKE__UNKNOWNMODEL",
    "beb6d3fb": "EGAUGE__4030",
    "fabfa505": "NCD__PR814SPST",
    "acd93fb3": "ADAFRUIT__642",
    "d0178dc3": "GRIDWORKS__TSNAP1",
    "f8b497e8": "GRIDWORKS__WATERTEMPHIGHPRECISION",
    "076da322": "GRIDWORKS__SIMPM1",
    "d300635e": "SCHNEIDERELECTRIC__IEM3455",
    "e81d74a8": "GRIDWORKS__SIMBOOL30AMPRELAY",
    "c75d269f": "OPENENERGY__EMONPI",
    "3042c432": "GRIDWORKS__SIMTSNAP1",
    "d0b0e375": "ATLAS__EZFLO",
    "4d649420": "HUBITAT__C7__LAN1",
    "bd759051": "GRIDWORKS__TANK_MODULE_1",
    "1f19839d": "FIBARO__ANALOG_TEMP_SENSOR",
    "46f21cd5": "AMPHENOL__NTC_10K_THERMISTOR_MA100GG103BN",
    "08da3f7d": "YHDC__SCT013100",
    "a8d9a70d": "MAGNELAB__SCT0300050",
    "bb31d136": "GRIDWORKS__MULTITEMP1",
    "3353ce46": "KRIDA__EMR16I2CV3",
    "5bd81968": "OMEGA__FTB8007HWPT",
    "99d961da": "ISTEC_4440",
    "39f97379": "OMEGA__FTB8010HWPT",
    "71a58010": "BELIMO__BALLVALVE232VS",
    "a156568f": "BELIMO__DIVERTERB332L",
    "94efd0b3": "TACO__0034EPLUS",
    "88e512cb": "TACO__007E",
    "22a3fc2a": "ARMSTRONG__COMPASSH",
    "d86abb96": "HONEYWELL__T6ZWAVETHERMOSTAT",
    "6a9541d9": "PRMFILTRATION__WM075",
    "e35655d0": "BELLGOSSETT__ECOCIRC20_18",
    "652abfd6": "TEWA__TT0P10KC3T1051500",
    "208f827f": "EKM__HOTSPWM075HD",
    "b3eced0d": "GRIDWORKS__SIMMULTITEMP",
    "e4807056": "GRIDWORKS__SIMTOTALIZER",
    "ff529d69": "KRIDA__DOUBLEEMR16I2CV3",
    "81d8b222": "GRIDWORKS__SIMDOUBLE16PINI2CRELAY",
    "d2d5023f": "GRIDWORKS__TANKMODULE2",
    "7d837129": "GRIDWORKS__PICOFLOWHALL",
    "5b11f334": "GRIDWORKS__PICOFLOWREED",
    "6cb4de48": "SAIER__SENHZG1WA",
}

value_to_symbol = {value: key for key, value in symbol_to_value.items()}

value_to_version = {
    "UNKNOWNMAKE__UNKNOWNMODEL": "000",
    "EGAUGE__4030": "000",
    "NCD__PR814SPST": "000",
    "ADAFRUIT__642": "000",
    "GRIDWORKS__TSNAP1": "000",
    "GRIDWORKS__WATERTEMPHIGHPRECISION": "000",
    "GRIDWORKS__SIMPM1": "000",
    "SCHNEIDERELECTRIC__IEM3455": "000",
    "GRIDWORKS__SIMBOOL30AMPRELAY": "000",
    "OPENENERGY__EMONPI": "000",
    "GRIDWORKS__SIMTSNAP1": "000",
    "ATLAS__EZFLO": "000",
    "HUBITAT__C7__LAN1": "001",
    "GRIDWORKS__TANK_MODULE_1": "001",
    "FIBARO__ANALOG_TEMP_SENSOR": "001",
    "AMPHENOL__NTC_10K_THERMISTOR_MA100GG103BN": "001",
    "YHDC__SCT013100": "001",
    "MAGNELAB__SCT0300050": "001",
    "GRIDWORKS__MULTITEMP1": "001",
    "KRIDA__EMR16I2CV3": "001",
    "OMEGA__FTB8007HWPT": "002",
    "ISTEC_4440": "002",
    "OMEGA__FTB8010HWPT": "002",
    "BELIMO__BALLVALVE232VS": "002",
    "BELIMO__DIVERTERB332L": "002",
    "TACO__0034EPLUS": "002",
    "TACO__007E": "002",
    "ARMSTRONG__COMPASSH": "002",
    "HONEYWELL__T6ZWAVETHERMOSTAT": "002",
    "PRMFILTRATION__WM075": "002",
    "BELLGOSSETT__ECOCIRC20_18": "002",
    "TEWA__TT0P10KC3T1051500": "002",
    "EKM__HOTSPWM075HD": "002",
    "GRIDWORKS__SIMMULTITEMP": "002",
    "GRIDWORKS__SIMTOTALIZER": "002",
    "KRIDA__DOUBLEEMR16I2CV3": "002",
    "GRIDWORKS__SIMDOUBLE16PINI2CRELAY": "002",
    "GRIDWORKS__TANKMODULE2": "003",
    "GRIDWORKS__PICOFLOWHALL": "003",
    "GRIDWORKS__PICOFLOWREED": "003",
    "SAIER__SENHZG1WA": "003",
}
