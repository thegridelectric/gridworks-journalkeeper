"""Tests synth.channel.gt type, version 000"""

from gjk.enums import TelemetryName
from gjk.named_types import SynthChannelGt


def test_synth_channel_gt_generated() -> None:
    d = {
        "Id": "99fb8f0e-3c7c-4b62-be5a-4f7a6376519f",
        "Name": "required-swt",
        "CreatedByNodeName": "synth-generator",
        "TelemetryName": "WaterTempFTimes1000",
        "TerminalAssetAlias": "d1.isone.ct.orange.ta",
        "Strategy": "simple",
        "DisplayName": "Required Source Water Temp",
        "SyncReportMinutes": 60,
        "TypeName": "synth.channel.gt",
        "Version": "000",
    }

    assert SynthChannelGt.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, TelemetryName="unknown_enum_thing")
    assert SynthChannelGt.from_dict(d2).telemetry_name == TelemetryName.default()
