"""
Tests for enum spaceheat.make.model.003 from the GridWorks Type Registry.
"""

from gjk.enums import MakeModel


def test_make_model() -> None:
    assert set(MakeModel.values()) == {
        "UNKNOWNMAKE__UNKNOWNMODEL",
        "EGAUGE__4030",
        "NCD__PR814SPST",
        "ADAFRUIT__642",
        "GRIDWORKS__TSNAP1",
        "GRIDWORKS__WATERTEMPHIGHPRECISION",
        "GRIDWORKS__SIMPM1",
        "SCHNEIDERELECTRIC__IEM3455",
        "GRIDWORKS__SIMBOOL30AMPRELAY",
        "OPENENERGY__EMONPI",
        "GRIDWORKS__SIMTSNAP1",
        "ATLAS__EZFLO",
        "HUBITAT__C7__LAN1",
        "GRIDWORKS__TANK_MODULE_1",
        "FIBARO__ANALOG_TEMP_SENSOR",
        "AMPHENOL__NTC_10K_THERMISTOR_MA100GG103BN",
        "YHDC__SCT013100",
        "MAGNELAB__SCT0300050",
        "GRIDWORKS__MULTITEMP1",
        "KRIDA__EMR16I2CV3",
        "OMEGA__FTB8007HWPT",
        "ISTEC_4440",
        "OMEGA__FTB8010HWPT",
        "BELIMO__BALLVALVE232VS",
        "BELIMO__DIVERTERB332L",
        "TACO__0034EPLUS",
        "TACO__007E",
        "ARMSTRONG__COMPASSH",
        "HONEYWELL__T6ZWAVETHERMOSTAT",
        "PRMFILTRATION__WM075",
        "BELLGOSSETT__ECOCIRC20_18",
        "TEWA__TT0P10KC3T1051500",
        "EKM__HOTSPWM075HD",
        "GRIDWORKS__SIMMULTITEMP",
        "GRIDWORKS__SIMTOTALIZER",
        "KRIDA__DOUBLEEMR16I2CV3",
        "GRIDWORKS__SIMDOUBLE16PINI2CRELAY",
        "GRIDWORKS__TANKMODULE2",
        "GRIDWORKS__PICOFLOWHALL",
        "GRIDWORKS__PICOFLOWREED",
        "SAIER__SENHZG1WA",
    }

    assert MakeModel.default() == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL
    assert MakeModel.enum_name() == "spaceheat.make.model"
    assert MakeModel.enum_version() == "003"

    assert MakeModel.version("UNKNOWNMAKE__UNKNOWNMODEL") == "000"
    assert MakeModel.version("EGAUGE__4030") == "000"
    assert MakeModel.version("NCD__PR814SPST") == "000"
    assert MakeModel.version("ADAFRUIT__642") == "000"
    assert MakeModel.version("GRIDWORKS__TSNAP1") == "000"
    assert MakeModel.version("GRIDWORKS__WATERTEMPHIGHPRECISION") == "000"
    assert MakeModel.version("GRIDWORKS__SIMPM1") == "000"
    assert MakeModel.version("SCHNEIDERELECTRIC__IEM3455") == "000"
    assert MakeModel.version("GRIDWORKS__SIMBOOL30AMPRELAY") == "000"
    assert MakeModel.version("OPENENERGY__EMONPI") == "000"
    assert MakeModel.version("GRIDWORKS__SIMTSNAP1") == "000"
    assert MakeModel.version("ATLAS__EZFLO") == "000"
    assert MakeModel.version("HUBITAT__C7__LAN1") == "001"
    assert MakeModel.version("GRIDWORKS__TANK_MODULE_1") == "001"
    assert MakeModel.version("FIBARO__ANALOG_TEMP_SENSOR") == "001"
    assert MakeModel.version("AMPHENOL__NTC_10K_THERMISTOR_MA100GG103BN") == "001"
    assert MakeModel.version("YHDC__SCT013100") == "001"
    assert MakeModel.version("MAGNELAB__SCT0300050") == "001"
    assert MakeModel.version("GRIDWORKS__MULTITEMP1") == "001"
    assert MakeModel.version("KRIDA__EMR16I2CV3") == "001"
    assert MakeModel.version("OMEGA__FTB8007HWPT") == "002"
    assert MakeModel.version("ISTEC_4440") == "002"
    assert MakeModel.version("OMEGA__FTB8010HWPT") == "002"
    assert MakeModel.version("BELIMO__BALLVALVE232VS") == "002"
    assert MakeModel.version("BELIMO__DIVERTERB332L") == "002"
    assert MakeModel.version("TACO__0034EPLUS") == "002"
    assert MakeModel.version("TACO__007E") == "002"
    assert MakeModel.version("ARMSTRONG__COMPASSH") == "002"
    assert MakeModel.version("HONEYWELL__T6ZWAVETHERMOSTAT") == "002"
    assert MakeModel.version("PRMFILTRATION__WM075") == "002"
    assert MakeModel.version("BELLGOSSETT__ECOCIRC20_18") == "002"
    assert MakeModel.version("TEWA__TT0P10KC3T1051500") == "002"
    assert MakeModel.version("EKM__HOTSPWM075HD") == "002"
    assert MakeModel.version("GRIDWORKS__SIMMULTITEMP") == "002"
    assert MakeModel.version("GRIDWORKS__SIMTOTALIZER") == "002"
    assert MakeModel.version("KRIDA__DOUBLEEMR16I2CV3") == "002"
    assert MakeModel.version("GRIDWORKS__SIMDOUBLE16PINI2CRELAY") == "002"
    assert MakeModel.version("GRIDWORKS__TANKMODULE2") == "003"
    assert MakeModel.version("GRIDWORKS__PICOFLOWHALL") == "003"
    assert MakeModel.version("GRIDWORKS__PICOFLOWREED") == "003"
    assert MakeModel.version("SAIER__SENHZG1WA") == "003"

    for value in MakeModel.values():
        symbol = MakeModel.value_to_symbol(value)
        assert MakeModel.symbol_to_value(symbol) == value
