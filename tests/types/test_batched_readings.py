"""Tests batched.readings type, version 000"""

import json

import pytest
from gjk.enums import TelemetryName
from gjk.types import BatchedReadings, ChannelReadings, DataChannelGt
from gjk.types import BatchedReadingsMaker as Maker
from gw.errors import GwTypeError
from pydantic import ValidationError


def test_batched_readings_generated() -> None:
    t = BatchedReadings(
        from_g_node_alias="hw1.isone.me.versant.keene.beech.scada",
        from_g_node_instance_id="98542a17-3180-4f2a-a929-6023f0e7a106",
        about_g_node_alias="hw1.isone.me.versant.keene.beech.ta",
        slot_start_unix_s=1708518780,
        batched_transmission_period_s=30,
        message_created_ms=1708518810017,
        data_channel_list=[
            DataChannelGt(
                name="hp-odu-pwr",
                display_name="HP ODU Power",
                about_node_name="hp-odu",
                captured_by_node_name="primary-pwr-meter",
                terminal_asset_alias="hw1.isone.me.versant.keene.beech.ta",
                in_power_metering=True,
                start_s=1704862800,
                telemetry_name=TelemetryName.PowerW,
                id="498da855-bac5-47e9-b83a-a11e56a50e67",
            ),
            DataChannelGt(
                name="hp-idu-pwr",
                display_name="HP IDU Power",
                about_node_name="hp-idu",
                captured_by_node_name="primary-pwr-meter",
                terminal_asset_alias="hw1.isone.me.versant.keene.beech.ta",
                in_power_metering=True,
                start_s=1704862800,
                telemetry_name=TelemetryName.PowerW,
                id="beabac86-7caa-4ab4-a50b-af1ad54ed165",
            ),
        ],
        channel_reading_list=[
            ChannelReadings(
                channel_id="498da855-bac5-47e9-b83a-a11e56a50e67",
                value_list=[26, 96, 196],
                scada_read_time_unix_ms_list=[
                    1708518800235,
                    1708518808236,
                    1708518809232,
                ],
            ),
            ChannelReadings(
                channel_id="beabac86-7caa-4ab4-a50b-af1ad54ed165",
                value_list=[14],
                scada_read_time_unix_ms_list=[1708518800235],
            ),
        ],
        fsm_action_list=[],
        fsm_report_list=[],
        id="4dab57dd-8b4e-4ea4-90a3-d63df9eeb061",
    )

    d = {
        "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
        "FromGNodeInstanceId": "98542a17-3180-4f2a-a929-6023f0e7a106",
        "AboutGNodeAlias": "hw1.isone.me.versant.keene.beech.ta",
        "SlotStartUnixS": 1708518780,
        "BatchedTransmissionPeriodS": 30,
        "MessageCreatedMs": 1708518810017,
        "DataChannelList": [
            {
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
            },
            {
                "Name": "hp-idu-pwr",
                "DisplayName": "HP IDU Power",
                "AboutNodeName": "hp-idu",
                "CapturedByNodeName": "primary-pwr-meter",
                "TerminalAssetAlias": "hw1.isone.me.versant.keene.beech.ta",
                "InPowerMetering": True,
                "StartS": 1704862800,
                "Id": "beabac86-7caa-4ab4-a50b-af1ad54ed165",
                "TypeName": "data.channel.gt",
                "Version": "001",
                "TelemetryNameGtEnumSymbol": "af39eec9",
            },
        ],
        "ChannelReadingList": [
            {
                "ChannelId": "498da855-bac5-47e9-b83a-a11e56a50e67",
                "ValueList": [26, 96, 196],
                "ScadaReadTimeUnixMsList": [
                    1708518800235,
                    1708518808236,
                    1708518809232,
                ],
                "TypeName": "channel.readings",
                "Version": "000",
            },
            {
                "ChannelId": "beabac86-7caa-4ab4-a50b-af1ad54ed165",
                "ValueList": [14],
                "ScadaReadTimeUnixMsList": [1708518800235],
                "TypeName": "channel.readings",
                "Version": "000",
            },
        ],
        "FsmActionList": [],
        "FsmReportList": [],
        "Id": "4dab57dd-8b4e-4ea4-90a3-d63df9eeb061",
        "TypeName": "batched.readings",
        "Version": "000",
    }

    assert t.as_dict() == d

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
    del d2["FromGNodeAlias"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["FromGNodeInstanceId"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["AboutGNodeAlias"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["SlotStartUnixS"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["BatchedTransmissionPeriodS"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["MessageCreatedMs"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["DataChannelList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["ChannelReadingList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["FsmActionList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["FsmReportList"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = d.copy()
    del d2["Id"]
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, SlotStartUnixS="1656945300.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, BatchedTransmissionPeriodS="300.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, MessageCreatedMs="1656945600044.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, DataChannelList="Not a list.")
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, DataChannelList=["Not a list of dicts"])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, DataChannelList=[{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ChannelReadingList="Not a list.")
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ChannelReadingList=["Not a list of dicts"])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ChannelReadingList=[{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FsmActionList="Not a list.")
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FsmActionList=["Not a list of dicts"])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FsmActionList=[{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FsmReportList="Not a list.")
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FsmReportList=["Not a list of dicts"])
    with pytest.raises(GwTypeError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FsmReportList=[{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(GwTypeError):
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

    d2 = dict(d, FromGNodeAlias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, FromGNodeInstanceId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, AboutGNodeAlias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, SlotStartUnixS=32503683600)
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, BatchedTransmissionPeriodS=0)
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, MessageCreatedMs=1656245000)
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, Id="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
