"""Tests flo.params.house0 type, version 000"""


def test_flo_params_house0_generated() -> None:
    ...
    # d = {
    #     "GNodeAlias": "d1.isone.ver.keene.holly",
    #     "FloParamsUid": "97eba574-bd20-45b5-bf82-9ba2f492d8f6",
    #     "TimezoneStr": ,
    #     "StartUnixS": 1734476700,
    #     "NumLayers": ,
    #     "HorizonHours": ,
    #     "StorageVolumeGallons": ,
    #     "StorageLossesPercent": ,
    #     "HpMinElecKw": ,
    #     "HpMaxElecKw": ,
    #     "CopIntercept": ,
    #     "CopOatCoeff": ,
    #     "CopLwtCoeff": ,
    #     "InitialTopTempF": ,
    #     "InitialThermocline": ,
    #     "LmpForecast": ,
    #     "DistPriceForecast": ,
    #     "RegPriceForecast": ,
    #     "PriceForecastUid": ,
    #     "OatForecastF": ,
    #     "WindSpeedForecastMph": ,
    #     "WeatherUid": ,
    #     "AlphaTimes10": ,
    #     "BetaTimes100": ,
    #     "GammaEx6": ,
    #     "IntermediatePowerKw": ,
    #     "IntermediateRswtF": ,
    #     "DdPowerKw": ,
    #     "DdRswtF": ,
    #     "DdDeltaTF": ,
    #     "MaxEwtF": ,
    #     "PriceUnit": ,
    #     "ParamsGeneratedS": ,
    #     "TypeName": "flo.params.house0",
    #     "Version": "000",
    # }

    # assert FloParamsHouse0.from_dict(d).to_dict() == d

    # ######################################
    # # Behavior on unknown enum values: sends to default
    # ######################################

    # d2 = dict(d, PriceUnit="unknown_enum_thing")
    # assert FloParamsHouse0.from_dict(d2).price_unit == MarketPriceUnit.default()
