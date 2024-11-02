"""Tests pico.flow.module.component.gt type, version 000"""

from gjk.enums import GpmFromHzMethod, HzCalcMethod, MakeModel
from gjk.named_types import PicoFlowModuleComponentGt


def test_pico_flow_module_component_gt_generated() -> None:
    d = {
        "Enabled": True,
        "SerialNumber": "NA",
        "FlowNodeName": "primary-flow",
        "FlowMeterType": "EKM__HOTSPWM075HD",
        "HzCalcMethod": "BasicExpWeightedAvg",
        "GpmFromHzMethod": "Constant",
        "ConstantGallonsPerTick": 0.0748,
        "SendHz": True,
        "SendGallons": False,
        "SendTickLists": False,
        "NoFlowMs": 5000,
        "AsyncCaptureThresholdGpmTimes100": 5,
        "PublishAnyTicklistAfterS": 10,
        "PublishTicklistLength": 10,
        "ExpAlpha": 0.5,
        "ComponentId": "b505a781-1671-467f-af8f-6d0ad7aca172",
        "ComponentAttributeClassId": "aa4ad342-883a-4f89-bf86-9eb430aeb308",
        "ConfigList": [
            {
                "AsyncCapture": True,
                "CapturePeriodS": 10,
                "ChannelName": "primary-flow",
                "Exponent": 2,
                "TypeName": "channel.config",
                "Unit": "Gpm",
                "Version": "000",
            },
            {
                "AsyncCapture": True,
                "CapturePeriodS": 10,
                "ChannelName": "primary-flow-hz",
                "Exponent": 6,
                "TypeName": "channel.config",
                "Unit": "VoltsRms",
                "Version": "000",
            },
        ],
        "DIsplayName": "Primary Flow ReedFlowModule",
        "TypeName": "pico.flow.module.component.gt",
        "Version": "000",
    }

    assert PicoFlowModuleComponentGt.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, FlowMeterType="unknown_enum_thing")
    assert (
        PicoFlowModuleComponentGt.from_dict(d2).flow_meter_type == MakeModel.default()
    )

    d2 = dict(d, HzCalcMethod="unknown_enum_thing")
    assert (
        PicoFlowModuleComponentGt.from_dict(d2).hz_calc_method == HzCalcMethod.default()
    )

    d2 = dict(d, GpmFromHzMethod="unknown_enum_thing")
    assert (
        PicoFlowModuleComponentGt.from_dict(d2).gpm_from_hz_method
        == GpmFromHzMethod.default()
    )
