"""Tests data.channel.gt type, version 001"""

import pytest
from gjk.enums import TelemetryName
from gjk.types import DataChannelGt
from gw.errors import GwTypeError


def test_data_channel_gt_generated() -> None:
    t = DataChannelGt(
        name="hp-idu-pwr",
        display_name="Hp IDU",
        about_node_name="hp-idu-pwr",
        captured_by_node_name="power-meter",
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias="hw1.isone.me.versant.keene.beech.ta",
        in_power_metering=True,
        start_s=1721405699,
        id="50cf426b-ff3f-4a30-8415-8d3fba5e0ab7",
    )

    d = {
        "Name": "hp-idu-pwr",
        "DisplayName": "Hp IDU",
        "AboutNodeName": "hp-idu-pwr",
        "CapturedByNodeName": "power-meter",
        "TelemetryName": "PowerW",
        "TerminalAssetAlias": "hw1.isone.me.versant.keene.beech.ta",
        "InPowerMetering": True,
        "StartS": 1721405699,
        "Id": "50cf426b-ff3f-4a30-8415-8d3fba5e0ab7",
        "TypeName": "data.channel.gt",
        "Version": "001",
    }

    assert t.to_dict() == d
    assert t == DataChannelGt.from_dict(d)

    d2 = d.copy()
    del d2["TelemetryName"]
    d2["TelemetryNameGtEnumSymbol"] = "af39eec9"
    assert t == DataChannelGt.from_dict(d2)

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, TelemetryName="unknown_enum_thing", InPowerMetering=False)
    assert DataChannelGt.from_dict(d2).telemetry_name == TelemetryName.default()

    d2 = dict(d, StartS="1721405699")
    with pytest.raises(GwTypeError):
        DataChannelGt.from_dict(d2)
