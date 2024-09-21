from typing import Dict, List, Optional

from deepdiff import DeepDiff
from gjk.codec import pyd_to_sql
from gjk.enums import TelemetryName
from gjk.first_season.alias_mapper import AliasMapper
from gjk.first_season.oak_names import OAK_TA, ON, OcName
from gjk.models import DataChannelSql
from gjk.types import DataChannelGt
from gw.errors import DcError
from sqlalchemy.orm import Session


def data_channels_match_db(
    session: Session,
    local_dcs: Optional[List[DataChannelSql]] = None,
    check_missing=True,
) -> None:
    """
    Raises exception if there is a mismatch between data channels
    in code and in database
    """
    consistent = True
    if local_dcs is None:
        local_dcs = {pyd_to_sql(dc) for dc in OAK_CHANNELS_BY_NAME.values()}

    dcs = set(dc for dc in session.query(DataChannelSql).all() if 'oak' in dc.terminal_asset_alias)

    local_ids = {dc.id for dc in local_dcs}
    ids = {dc.id for dc in dcs}

    # look for missing local channels
    if check_missing:
        if (ids - local_ids) != set():
            consistent = False
            print("Missing some channels locally")
            for id in ids - local_ids:
                dc = next(dc for dc in dcs if dc.id == id)
                print(dc.to_dict())

    # look for missing global channels
    if (local_ids - ids) != set():
        consistent = False
        print("Missing some channels in db")
        for id in local_ids - ids:
            dc = next(dc for dc in local_dcs if dc.id == id)
            print(dc.to_dict())

    # look for mismatches
    for id in local_ids & ids:
        dc_local = next(dc for dc in local_dcs if dc.id == id)
        dc = next(dc for dc in dcs if dc.id == id)
        dc_local_dict = dc_local.to_dict()
        dc_local_dict.pop("DisplayName")
        dc_dict = dc.to_dict()
        dc_dict.pop("DisplayName")

        # InPowerMetering is optional
        if "InPowerMetering" in dc_dict:
            dc_dict.pop("InPowerMetering")
        if "InPowerMetering" in dc_local_dict:
            dc_local_dict.pop("InPowerMetering")

        if dc_local_dict != dc_dict:
            consistent = False
            print("Inconsistency!\n\n")
            print(f"   Local: {dc_local_dict}")
            print(f"   Global: {dc_dict}")
            diff = DeepDiff(dc_local_dict, dc_dict)
            print("\n\nDiff:")
            print(diff)
    if not consistent:
        raise DcError("local and global data channels for oak do not match")


OAK_CHANNELS_BY_NAME: Dict[str, DataChannelGt] = {
    OcName.ZONE['up'].NAME: DataChannelGt(
        id="c2b54623-4c9d-4b23-bf37-447190d058d2",
        name=OcName.ZONE['up'].STATE,
        display_name="Up Zone Honeywell Heat Call State",
        about_node_name=ON.TEMP.ZONE['up'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['up'].STAT,
        telemetry_name=TelemetryName.ThermostatState,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['down'].NAME: DataChannelGt(
        id="37154ab8-1166-41ef-bdb2-3fa116049990",
        name=OcName.ZONE['down'].STATE,
        display_name="Down Zone Honeywell Heat Call State",
        about_node_name=ON.TEMP.ZONE['down'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['down'].STAT,
        telemetry_name=TelemetryName.ThermostatState,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.STORE_PUMP_PWR: DataChannelGt(
        id="b4d40404-dc8f-4353-9cd6-3eea4457eae9",
        name=OcName.STORE_PUMP_PWR,
        display_name="Store pump power",
        about_node_name=ON.STORE_PUMP,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.PRIMARY_PUMP_PWR: DataChannelGt(
        id="55173ca8-ac64-424a-9b74-652c60971826",
        name=OcName.PRIMARY_PUMP_PWR,
        display_name="Primary pump power",
        about_node_name=ON.PRIMARY_PUMP,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.DIST_PUMP_PWR: DataChannelGt(
        id="aeace76a-ff0a-49d8-8643-426e6890cafd",
        name=OcName.DIST_PUMP_PWR,
        display_name="Distribution pump power",
        about_node_name=ON.DIST_PUMP,
        captured_by_node_name=ON.DIST_PUMP,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    # OcName.AMPHA_DIST_SWT: DataChannelGt(
    #     id="38e95a83-270c-4520-af1a-b85a07a3c02f",
    #     name=OcName.AMPHA_DIST_SWT,
    #     display_name="Dist SWT measured with an AmphA",
    #     about_node_name=BN.AMPHA_DIST_SWT,
    #     captured_by_node_name=ON.ANALOG_TEMP,
    #     telemetry_name=TelemetryName.WaterTempCTimes1000,
    #     terminal_asset_alias=OAK_TA,
    # ),
    # OcName.AMPHB_DIST_SWT: DataChannelGt(
    #     id="934c04d3-2a06-475d-a708-5129979ceedf",
    #     name=OcName.AMPHB_DIST_SWT,
    #     display_name="Dist SWT measured with an Amphb",
    #     about_node_name=BN.AMPHB_DIST_SWT,
    #     captured_by_node_name=ON.ANALOG_TEMP,
    #     telemetry_name=TelemetryName.WaterTempCTimes1000,
    #     terminal_asset_alias=OAK_TA,
    # ),
    OcName.HP_ODU_PWR: DataChannelGt(
        id="299a47c4-9d2a-45f7-9b68-60334742853e",
        name=OcName.HP_ODU_PWR,
        display_name="HP ODU Power",
        about_node_name=ON.HP_ODU,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
        in_power_metering=True,
    ),
    OcName.HP_IDU_PWR: DataChannelGt(
        id="b2a8d472-c4f1-4476-8524-3a24782a4c7e",
        name=OcName.HP_IDU_PWR,
        display_name="HP IDU Power",
        about_node_name=ON.HP_IDU,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
        in_power_metering=True,
    ),
    OcName.BUFFER_WELL_TEMP: DataChannelGt(
        id="ba620238-63c6-4e38-903e-3e2755b8a779",
        name=OcName.BUFFER_WELL_TEMP,
        display_name="Buffer Well Temp",
        about_node_name=ON.BUFFER_WELL,
        captured_by_node_name=ON.BUFFER_WELL,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    # OcName.OIL_BOILER_FLOW_INTEGRATED: DataChannelGt(
    #     id="251871dd-6dc8-40d9-a811-f62319461435",
    #     name=OcName.OIL_BOILER_FLOW_INTEGRATED,
    #     display_name="Oil Boiler Integrated Flow",
    #     about_node_name=BN.OIL_BOILER_FLOW,
    #     captured_by_node_name=BN.OIL_BOILER_FLOW,
    #     telemetry_name=TelemetryName.GallonsTimes100,
    #     terminal_asset_alias=OAK_TA,
    # ),
    OcName.ZONE['down'].SET: DataChannelGt(
        id="44f85516-cab9-47ef-be3f-ffa79a03ace1",
        name=OcName.ZONE['down'].SET,
        display_name="Down Zone Honeywell Setpoint",
        about_node_name=ON.TEMP.ZONE['down'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['down'].STAT,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['down'].TEMP: DataChannelGt(
        id="1a99c18e-c409-4344-b87d-fe932038c39f",
        name=OcName.ZONE['down'].TEMP,
        display_name="Down Zone Honeywell Temp",
        about_node_name=ON.TEMP.ZONE['down'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['down'].NAME,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['up'].SET: DataChannelGt(
        id="d2158a1b-0459-4b0f-a67b-395e79136330",
        name=OcName.ZONE['up'].SET,
        display_name="Up Zone Honeywell Setpoint",
        about_node_name=ON.TEMP.ZONE['up'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['up'].STAT,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['up'].TEMP: DataChannelGt(
        id="91d9fca3-c823-42aa-a8a0-a6b8c267e415",
        name=OcName.ZONE['up'].TEMP,
        display_name="Up Zone Honeywell Temp",
        about_node_name=ON.TEMP.ZONE['up'].STAT,
        captured_by_node_name=OcName.ZONE['up'].NAME,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['living-room'].SET: DataChannelGt(
        id="42177a16-edea-41e0-bbcb-b200d762af5d",
        name=OcName.ZONE['living-room'].SET,
        display_name="Living room Zone Honeywell Setpoint",
        about_node_name=ON.TEMP.ZONE['living-room'].STAT,
        captured_by_node_name=OcName.ZONE['living-room'].STAT,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['living-room'].TEMP: DataChannelGt(
        id="f316b3c4-3f9c-4d8a-a862-7074aeda1f86",
        name=OcName.ZONE['living-room'].TEMP,
        display_name="Living room Zone Honeywell Temp",
        about_node_name=ON.TEMP.ZONE['living-room'].STAT,
        captured_by_node_name=OcName.ZONE['living-room'].NAME,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['garage'].SET: DataChannelGt(
        id="4b5b5534-39a9-4424-b79a-b1611438283d",
        name=OcName.ZONE['garage'].SET,
        display_name="Garage Zone Honeywell Setpoint",
        about_node_name=ON.TEMP.ZONE['garage'].STAT,
        captured_by_node_name=OcName.ZONE['garage'].STAT,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['garage'].TEMP: DataChannelGt(
        id="971a2c41-a459-4857-a9c0-ad3b6b2eb5dc",
        name=OcName.ZONE['garage'].TEMP,
        display_name="Garage Zone Honeywell Temp",
        about_node_name=ON.TEMP.ZONE['garage'].STAT,
        captured_by_node_name=OcName.ZONE['garage'].NAME,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.OIL_BOILER_PWR: DataChannelGt(
        id="960beace-27fd-4038-8579-74b0afe6f578",
        name=OcName.OIL_BOILER_PWR,
        display_name="Oil Boiler pump power",
        about_node_name=ON.OIL_BOILER,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_COLD_PIPE: DataChannelGt(
        id="9eb57c30-7339-4c08-8fc1-0f7371f09a58",
        name=OcName.BUFFER_COLD_PIPE,
        display_name="Buffer Cold (C x 1000)",
        about_node_name=ON.BUFFER_COLD_PIPE,
        captured_by_node_name=ON.BUFFER_COLD_PIPE,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_HOT_PIPE: DataChannelGt(
        id="d9d6ff80-3da1-4b71-8630-32d4b6020b43",
        name=OcName.BUFFER_HOT_PIPE,
        display_name="Buffer Hot (C x 1000)",
        about_node_name=ON.BUFFER_HOT_PIPE,
        captured_by_node_name=ON.BUFFER_HOT_PIPE,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_DEPTH1_TEMP: DataChannelGt(
        id="21936d6b-869b-4dc1-b501-20c76782589f",
        name=OcName.BUFFER_DEPTH1_TEMP,
        display_name="Buffer Depth 1 (C x 1000)",
        about_node_name=ON.TEMP.BUFFER_DEPTH1,
        captured_by_node_name=ON.BUFFER_TANK_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_DEPTH2_TEMP: DataChannelGt(
        id="f5a0c2ce-7e8f-4efa-842e-81a7e15a5196",
        name=OcName.BUFFER_DEPTH2_TEMP,
        display_name="Buffer Depth 2 (C x 1000)",
        about_node_name=ON.TEMP.BUFFER_DEPTH2,
        captured_by_node_name=ON.BUFFER_TANK_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_DEPTH3_TEMP: DataChannelGt(
        id="79c30451-cfaf-409d-9b74-78a3e6619f0c",
        name=OcName.BUFFER_DEPTH3_TEMP,
        display_name="Buffer Depth 3 (C x 1000)",
        about_node_name=ON.TEMP.BUFFER_DEPTH3,
        captured_by_node_name=ON.BUFFER_TANK_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_DEPTH4_TEMP: DataChannelGt(
        id="ad86f200-f4b5-4eae-b987-6e925efae172",
        name=OcName.BUFFER_DEPTH4_TEMP,
        display_name="Buffer Depth 4 (C x 1000)",
        about_node_name=ON.TEMP.BUFFER_DEPTH4,
        captured_by_node_name=ON.BUFFER_TANK_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_WELL_TEMP: DataChannelGt(
        id="aedfa460-849f-4297-8428-13ba10e99f9e",
        name=OcName.BUFFER_WELL_TEMP,
        display_name="Buffer Well (C x 1000)",
        about_node_name=ON.BUFFER_WELL,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.DIST_RWT: DataChannelGt(
        id="5df1a8dd-f5dc-496c-928b-f4e98553005d",
        name=OcName.DIST_RWT,
        display_name="Dist RWT (C x 1000)",
        about_node_name=ON.DIST_RWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.DIST_SWT: DataChannelGt(
        id="6eb54a9d-50d3-4854-b388-3b635813edd5",
        name=OcName.DIST_SWT,
        display_name="Dist SWT (C x 1000)",
        about_node_name=ON.DIST_SWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['up'].GW_TEMP: DataChannelGt(
        id="3eca0062-4885-4687-b29a-d6a1af8f777a",
        name=OcName.ZONE['up'].GW_TEMP,
        display_name="Upstairs Zone Temp (C x 1000)",
        about_node_name=ON.TEMP.ZONE['up'].NAME,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['down'].GW_TEMP: DataChannelGt(
        id="4d164537-4466-4e0e-9517-9ead63698f38",
        name=OcName.ZONE['down'].GW_TEMP,
        display_name="Downstairs Zone Temp (C x 1000)",
        about_node_name=ON.TEMP.ZONE['up'].STAT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.HP_EWT: DataChannelGt(
        id="7c9d7fe3-2e16-45e6-ab5d-2ee9468dbd71",
        name=OcName.HP_EWT,
        display_name="HP EWT (C x 1000)",
        about_node_name=ON.HP_EWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.HP_LWT: DataChannelGt(
        id="8d55e3f6-13eb-4297-9618-9ac08f1e575b",
        name=OcName.HP_LWT,
        display_name="HP EWT (C x 1000)",
        about_node_name=ON.HP_LWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.STORE_COLD_PIPE: DataChannelGt(
        id="3d9d5b42-d03a-4b3a-9697-edc7d8a21faf",
        name=OcName.STORE_COLD_PIPE,
        display_name="Store Cold Pipe (C x 1000)",
        about_node_name=ON.STORE_COLD_PIPE,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.STORE_HOT_PIPE: DataChannelGt(
        id="bdb37789-b64e-44cc-aeb9-e277909709c5",
        name=OcName.STORE_HOT_PIPE,
        display_name="Store Hot Pipe (C x 1000)",
        about_node_name=ON.STORE_HOT_PIPE,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[1].depth1: DataChannelGt(
        id="a795290b-4743-4aed-8431-cee0b17c64c3",
        name=OcName.TANK[1].depth1,
        display_name="Tank 1 Depth 1 (C x 1000)",
        about_node_name=ON.TEMP.TANK[1].depth1,
        captured_by_node_name=ON.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[1].depth2: DataChannelGt(
        id="f7e93847-5d0b-42f9-9f9e-ca6d918904a1",
        name=OcName.TANK[1].depth2,
        display_name="Tank 1 Depth 2 (C x 1000)",
        about_node_name=ON.TEMP.TANK[1].depth2,
        captured_by_node_name=ON.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[1].depth3: DataChannelGt(
        id="bf793144-60b3-46c9-8389-d40bae6698a0",
        name=OcName.TANK[1].depth3,
        display_name="Tank 1 Depth 3 (C x 1000)",
        about_node_name=ON.TEMP.TANK[1].depth3,
        captured_by_node_name=ON.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[1].depth4: DataChannelGt(
        id="90b0336c-562c-471c-bba3-4849b5177aa5",
        name=OcName.TANK[1].depth4,
        display_name="Tank 1 Depth 4 (C x 1000)",
        about_node_name=ON.TEMP.TANK[1].depth4,
        captured_by_node_name=ON.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[2].depth1: DataChannelGt(
        id="b93ded06-9ba3-41d9-ac88-cd9363c19cdf",
        name=OcName.TANK[2].depth1,
        display_name="Tank 2 Depth 1 (C x 1000)",
        about_node_name=ON.TEMP.TANK[2].depth1,
        captured_by_node_name=ON.TANK2_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[2].depth2: DataChannelGt(
        id="ac471b36-790f-4f0d-b1b0-70ed038a266f",
        name=OcName.TANK[2].depth2,
        display_name="Tank 2 Depth 2 (C x 1000)",
        about_node_name=ON.TEMP.TANK[2].depth2,
        captured_by_node_name=ON.TANK2_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[2].depth3: DataChannelGt(
        id="6c9e22d8-8a54-42d9-858e-7d83a7665ca4",
        name=OcName.TANK[2].depth3,
        display_name="Tank 2 Depth 3 (C x 1000)",
        about_node_name=ON.TEMP.TANK[2].depth3,
        captured_by_node_name=ON.TANK2_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[2].depth4: DataChannelGt(
        id="f1f5202a-2eff-434f-84d7-71ee0773036e",
        name=OcName.TANK[2].depth4,
        display_name="Tank 2 Depth 4 (C x 1000)",
        about_node_name=ON.TEMP.TANK[2].depth4,
        captured_by_node_name=ON.TANK2_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[3].depth1: DataChannelGt(
        id="cf5e185c-c6e7-4e67-80ea-d423dc226dfb",
        name=OcName.TANK[3].depth1,
        display_name="Tank 3 Depth 1 (C x 1000)",
        about_node_name=ON.TEMP.TANK[3].depth1,
        captured_by_node_name=ON.TANK3_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[3].depth2: DataChannelGt(
        id="e104bee6-abde-4004-9f60-563bed779c94",
        name=OcName.TANK[3].depth2,
        display_name="Tank 3 Depth 2 (C x 1000)",
        about_node_name=ON.TEMP.TANK[3].depth2,
        captured_by_node_name=ON.TANK3_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[3].depth3: DataChannelGt(
        id="099aa9c1-97a5-4e61-bce1-81933b5096d6",
        name=OcName.TANK[3].depth3,
        display_name="Tank 3 Depth 3 (C x 1000)",
        about_node_name=ON.TEMP.TANK[3].depth3,
        captured_by_node_name=ON.TANK3_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[3].depth4: DataChannelGt(
        id="5a2abdd5-9295-4ea5-a83c-1e8188e3f382",
        name=OcName.TANK[3].depth4,
        display_name="Tank 3 Depth 4 (C x 1000)",
        about_node_name=ON.TEMP.TANK[3].depth4,
        captured_by_node_name=ON.TANK3_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.OAT: DataChannelGt(
        id="b3cb7460-cf74-40b3-afd0-42a5e236ba0b",
        name=OcName.OAT,
        display_name="Outside Air Temp (C x 1000)",
        about_node_name=ON.TEMP.OAT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.HP_FOSSIL_LWT:
    # Non-essential temperatures
    DataChannelGt(
        id="a5e82dbd-7956-4d5d-926d-2c1db9bec7e2",
        name=OcName.HP_FOSSIL_LWT,
        display_name="HeatPump Fossil LWT(C x 1000)",
        about_node_name=ON.HP_FOSSIL_LWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    # Integrated Flow
    OcName.DIST_FLOW_INTEGRATED: DataChannelGt(
        id="648fcb3a-80b6-4886-9567-af6197021ce9",
        name=OcName.DIST_FLOW_INTEGRATED,
        display_name="Distribution Gallons x 100",
        about_node_name=ON.DIST_FLOW,
        captured_by_node_name=ON.DIST_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.PRIMARY_FLOW_INTEGRATED: DataChannelGt(
        id="1a8d2419-4704-46aa-b7ee-27d148e6a07e",
        name=OcName.PRIMARY_FLOW_INTEGRATED,
        display_name="Primary Gallons x 100",
        about_node_name=ON.PRIMARY_FLOW,
        captured_by_node_name=ON.PRIMARY_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.STORE_FLOW_INTEGRATED: DataChannelGt(
        id="b52dc84b-47c5-477b-8a65-eb60b62b5948",
        name=OcName.STORE_FLOW_INTEGRATED,
        display_name="Store Gallons x 100",
        about_node_name=ON.STORE_FLOW,
        captured_by_node_name=ON.STORE_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.HOUSE_PANEL_PWR: DataChannelGt(
        id="69a485b0-6e60-4eae-b417-0c787ae35cd4",
        name=OcName.HOUSE_PANEL_PWR,
        display_name="House Panel Power",
        about_node_name=ON.HOUSE_PANEL,
        captured_by_node_name=ON.HOUSE_PANEL,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
}


OakAliasMapper = AliasMapper(scada="oak")
OakAliasMapper.channel_mappings = {
    OcName.PRIMARY_FLOW_INTEGRATED: [
        (1701406790, "a.primary.flow"),  #
    ],
    OcName.STORE_FLOW_INTEGRATED: [
        (1701406790, "a.store.flow"),  # 
    ],
    OcName.HP_LWT: [
        (1701406790, "a.hp.lwt.temp"),  # 
    ],
    OcName.HP_EWT: [
        (1701406790, "a.hp.ewt.temp"),  # 
    ],
    OcName.STORE_HOT_PIPE: [
        (1701406790, "a.store.hot.pipe.temp"),  # 
    ],
    OcName.STORE_COLD_PIPE: [
        (1701406790, "a.store.cold.pipe.temp"),  # 
    ],
    OcName.BUFFER_HOT_PIPE: [
        (1701406790, "a.buffer.hot.pipe.temp"),  # 
    ],
    OcName.BUFFER_COLD_PIPE: [
        (1701406790, "a.buffer.cold.pipe.temp"),  # 
    ],
    OcName.HP_FOSSIL_LWT: [
        (1701406790, "a.hp.fossil.lwt.temp"),  # 
    ],
    OcName.OAT: [
        (1701406790, "a.oat.temp")  #
    ],
    OcName.ZONE['down'].GW_TEMP: [
        (1701406790, "statcheck"),  #
    ],
    OcName.OIL_BOILER_PWR: [
        (1701406800, "a.m.oil.boiler.power"),  # 
    ],
    OcName.DIST_SWT: [
        (1701406800, "a.dist.swt.temp"),  # 
    ],
    OcName.DIST_RWT: [
        (1701406800, "a.dist.rwt.temp"),  # 
    ],
    OcName.DIST_FLOW_INTEGRATED: [
        (1701406810, "a.dist.flow"),  # 
    ],
    OcName.ZONE['living-room'].TEMP: [
        (1701406840, "a.thermostat.living.room.temp"),  # 
    ],
    OcName.ZONE['living-room'].SET: [
        (1701406840, "a.thermostat.living.room.set"),  # 
    ],
    OcName.ZONE['garage'].TEMP: [
        (1701406840, 'a.thermostat.garage.temp')
    ],
    OcName.ZONE['garage'].SET: [
        (1701406840, 'a.thermostat.garage.set')
    ],
    OcName.HP_ODU_PWR: [
        (1701406870, "a.m.hp.outdoor.power")
    ],
    OcName.HP_IDU_PWR: [
        (1701406870, "a.m.hp.indoor.power")
    ],
    OcName.DIST_PUMP_PWR:[
        (1701406870, "a.m.dist.pump.power")
    ],
    OcName.PRIMARY_PUMP_PWR:[
        (1701406870, "a.m.primary.pump.power")
    ],
    OcName.STORE_PUMP_PWR:[
        (1701406870, "a.m.store.pump.power")
    ],
    OcName.HOUSE_PANEL_PWR:[
        (1701406900, "a.m.house.panel.power")
    ]
}



if __name__ == '__main__':

    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy import create_engine
    import dotenv
    import os 
    from gjk.codec import pyd_to_sql

    dotenv.load_dotenv()
    engine = create_engine(os.getenv("GJK_DB_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()

    from gjk.models import bulk_insert_datachannels
    datachannel_list = [pyd_to_sql(value) for value in OAK_CHANNELS_BY_NAME.values()]
    bulk_insert_datachannels(session, datachannel_list)