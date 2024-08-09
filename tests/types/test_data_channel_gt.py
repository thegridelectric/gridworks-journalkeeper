"""Tests data.channel.gt type, version 001"""

import json

import pytest
from gjk.enums import TelemetryName
from gjk.types import DataChannelGt
from gjk.types import DataChannelGtMaker as Maker
from gw.errors import GwTypeError
from pydantic import ValidationError


def test_data_channel_gt_generated() -> None:
    t = DataChannelGt(
        name="hp-odu-pwr",
        display_name="HP ODU Power",
        about_node_name="hp-odu",
        captured_by_node_name="primary-pwr-meter",
        terminal_asset_alias="hw1.isone.me.versant.keene.beech.ta",
        in_power_metering=True,
        start_s=1704862800,
        telemetry_name=TelemetryName.PowerW,
        id="498da855-bac5-47e9-b83a-a11e56a50e67",
    )

    d = {
        "Name": "hp-odu-pwr",
        "DisplayName": "HP ODU Power",
        "AboutNodeName": "hp-odu",
        "CapturedByNodeName": "primary-pwr-meter",
        "TerminalAssetAlias": "hw1.isone.me.versant.keene.beech.ta",
        "InPowerMetering": True,
        "StartS": 1704862800,
        "Id": "498da855-bac5-47e9-b83a-a11e56a50e67",
        "TypeName": "data.channel.gt",
        "Version": "001",
        "TelemetryNameGtEnumSymbol": "af39eec9",
    }

    assert t.as_dict() == d

    d2 = d.copy()

    del d2["TelemetryNameGtEnumSymbol"]
    d2["TelemetryName"] = TelemetryName.PowerW.value
    assert t == Maker.dict_to_tuple(d2)

    with pytest.raises(GwTypeError):
        Maker.type_to_tuple(d)

    with pytest.raises(GwTypeError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gtype = json.dumps(d)
    gtuple = Maker.type_to_tuple(gtype)
    assert gtuple == t

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gtuple)) == gtuple

    ######################################
    # GwTypeError raised if missing a required attribute
    ######################################

    d2 = d.copy()
    del d2["TypeName"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["Name"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["DisplayName"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["AboutNodeName"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["CapturedByNodeName"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TelemetryNameGtEnumSymbol"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["TerminalAssetAlias"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["Id"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "StartS" in d2.keys():
        del d2["StartS"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, TelemetryNameGtEnumSymbol="unknown_symbol")
    assert Maker.dict_to_tuple(d2).telemetry_name == TelemetryName.default()

    d2 = dict(d, InPowerMetering="this is not a boolean")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, StartS="1721405699.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # ValidationError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type name")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # ValidationError raised if primitive attributes do not have appropriate property_format
    ######################################

    d2 = dict(d, Name="A.hot-stuff")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, AboutNodeName="A.hot-stuff")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, CapturedByNodeName="A.hot-stuff")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, TerminalAssetAlias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, StartS=32503683600)
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, Id="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
