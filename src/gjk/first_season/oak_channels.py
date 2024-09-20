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

    dcs = set(session.query(DataChannelSql).all())

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
        id="f8f5944f-d1f7-4f82-bca6-ce47aa90cefd",
        name=OcName.ZONE['up'].STATE,
        display_name="Up Zone Honeywell Heat Call State",
        about_node_name=ON.TEMP.ZONE['up'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['up'].STAT,
        telemetry_name=TelemetryName.ThermostatState,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['down'].NAME: DataChannelGt(
        id="eaec11a2-bf39-4487-bc25-9e7999d640c1",
        name=OcName.ZONE['down'].STATE,
        display_name="Down Zone Honeywell Heat Call State",
        about_node_name=ON.TEMP.ZONE['down'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['down'].STAT,
        telemetry_name=TelemetryName.ThermostatState,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.STORE_PUMP_PWR: DataChannelGt(
        id="ac35c2a9-e317-45e8-a036-52fa5cbd8380",
        name=OcName.STORE_PUMP_PWR,
        display_name="Store pump power",
        about_node_name=ON.STORE_PUMP,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.PRIMARY_PUMP_PWR: DataChannelGt(
        id="1e3c34e3-1e83-4dae-bfe3-a698c4618b5a",
        name=OcName.PRIMARY_PUMP_PWR,
        display_name="Primary pump power",
        about_node_name=ON.PRIMARY_PUMP,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.DIST_PUMP_PWR: DataChannelGt(
        id="a2ebe9fa-05ba-4665-a6ba-dbc85aee530c",
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
        id="498da855-bac5-47e9-b83a-a11e56a50e67",
        name=OcName.HP_ODU_PWR,
        display_name="HP ODU Power",
        about_node_name=ON.HP_ODU,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
        in_power_metering=True,
    ),
    OcName.HP_IDU_PWR: DataChannelGt(
        id="beabac86-7caa-4ab4-a50b-af1ad54ed165",
        name=OcName.HP_IDU_PWR,
        display_name="HP IDU Power",
        about_node_name=ON.HP_IDU,
        captured_by_node_name=ON.PRIMARY_POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
        in_power_metering=True,
    ),
    OcName.BUFFER_WELL_TEMP: DataChannelGt(
        id="8120ae8d-0029-4c85-bca1-9a70235bf423",
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
        id="dd4c0d78-d2e0-490c-b064-2f33b85ec431",
        name=OcName.ZONE['down'].SET,
        display_name="Down Zone Honeywell Setpoint",
        about_node_name=ON.TEMP.ZONE['down'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['down'].STAT,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['down'].TEMP: DataChannelGt(
        id="0334a75a-48ee-4da1-8b77-96fe05b0c3db",
        name=OcName.ZONE['down'].TEMP,
        display_name="Down Zone Honeywell Temp",
        about_node_name=ON.TEMP.ZONE['down'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['down'].STAT,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['up'].SET: DataChannelGt(
        id="581f758b-632f-426a-aebc-7432c416a99e",
        name=OcName.ZONE['up'].SET,
        display_name="Up Zone Honeywell Setpoint",
        about_node_name=ON.TEMP.ZONE['up'].STAT,
        captured_by_node_name=ON.TEMP.ZONE['up'].STAT,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['up'].TEMP: DataChannelGt(
        id="2196a6b7-90d1-42d0-b3f0-748f393bb35a",
        name=OcName.ZONE['up'].TEMP,
        display_name="Up Zone Honeywell Temp",
        about_node_name=ON.TEMP.ZONE['up'].STAT,
        captured_by_node_name=OcName.ZONE['up'].STAT,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    # OcName.OIL_BOILER_PWR: DataChannelGt(
    #     id="83fe770f-e022-4ad6-a471-cfb83e1b64be",
    #     name=OcName.OIL_BOILER_PWR,
    #     display_name="Oil Boiler pump power",
    #     about_node_name=BN.OIL_BOILER,
    #     captured_by_node_name=ON.PRIMARY_POWER_METER,
    #     telemetry_name=TelemetryName.PowerW,
    #     terminal_asset_alias=OAK_TA,
    # ),
    OcName.BUFFER_COLD_PIPE: DataChannelGt(
        id="a47abb1a-06fc-4d9b-a548-8531c482d3f2",
        name=OcName.BUFFER_COLD_PIPE,
        display_name="Buffer Cold (C x 1000)",
        about_node_name=ON.BUFFER_COLD_PIPE,
        captured_by_node_name=ON.BUFFER_COLD_PIPE,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_HOT_PIPE: DataChannelGt(
        id="cb542708-ba47-4c8b-9261-029dae126d6f",
        name=OcName.BUFFER_HOT_PIPE,
        display_name="Buffer Hot (C x 1000)",
        about_node_name=ON.BUFFER_HOT_PIPE,
        captured_by_node_name=ON.BUFFER_HOT_PIPE,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_DEPTH1_TEMP: DataChannelGt(
        id="17c338be-f09f-40c0-b99b-3a8d11076a1e",
        name=OcName.BUFFER_DEPTH1_TEMP,
        display_name="Buffer Depth 1 (C x 1000)",
        about_node_name=ON.TEMP.BUFFER_DEPTH1,
        captured_by_node_name=ON.BUFFER_TANK_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_DEPTH2_TEMP: DataChannelGt(
        id="064e5051-f724-4c65-b28f-d890afd7b3e4",
        name=OcName.BUFFER_DEPTH2_TEMP,
        display_name="Buffer Depth 2 (C x 1000)",
        about_node_name=ON.TEMP.BUFFER_DEPTH2,
        captured_by_node_name=ON.BUFFER_TANK_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_DEPTH3_TEMP: DataChannelGt(
        id="15ef5472-9530-4e91-b8c6-6434101fc113",
        name=OcName.BUFFER_DEPTH3_TEMP,
        display_name="Buffer Depth 3 (C x 1000)",
        about_node_name=ON.TEMP.BUFFER_DEPTH3,
        captured_by_node_name=ON.BUFFER_TANK_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_DEPTH4_TEMP: DataChannelGt(
        id="44a834d9-8052-4f21-9512-3b2579ba8491",
        name=OcName.BUFFER_DEPTH4_TEMP,
        display_name="Buffer Depth 4 (C x 1000)",
        about_node_name=ON.TEMP.BUFFER_DEPTH4,
        captured_by_node_name=ON.BUFFER_TANK_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.BUFFER_WELL_TEMP: DataChannelGt(
        id="f908be82-f8ac-42e7-8203-7057eeef79a8",
        name=OcName.BUFFER_WELL_TEMP,
        display_name="Buffer Well (C x 1000)",
        about_node_name=ON.BUFFER_WELL,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.DIST_RWT: DataChannelGt(
        id="2fe25fbf-400a-418e-b2dc-35e3b62f8250",
        name=OcName.DIST_RWT,
        display_name="Dist RWT (C x 1000)",
        about_node_name=ON.DIST_RWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.DIST_SWT: DataChannelGt(
        id="5dae9382-a2b1-4f11-9259-3f3f026944ab",
        name=OcName.DIST_SWT,
        display_name="Dist SWT (C x 1000)",
        about_node_name=ON.DIST_SWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['up'].GW_TEMP: DataChannelGt(
        id="0d9c3cac-5813-4881-a0f7-35d90ac4bd49",
        name=OcName.ZONE['up'].GW_TEMP,
        display_name="Upstairs Zone Temp (C x 1000)",
        about_node_name=ON.TEMP.ZONE['up'].NAME,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.ZONE['down'].GW_TEMP: DataChannelGt(
        id="01af1b8d-d22a-47c6-8e25-421be9df09b6",
        name=OcName.ZONE['down'].GW_TEMP,
        display_name="Downstairs Zone Temp (C x 1000)",
        about_node_name=ON.TEMP.ZONE['up'].STAT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.HP_EWT: DataChannelGt(
        id="cecc9b94-9b4b-45ce-a8e9-4c63d24530aa",
        name=OcName.HP_EWT,
        display_name="HP EWT (C x 1000)",
        about_node_name=ON.HP_EWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.HP_LWT: DataChannelGt(
        id="a49db047-e38f-44a4-b773-29102c2fc526",
        name=OcName.HP_LWT,
        display_name="HP EWT (C x 1000)",
        about_node_name=ON.HP_LWT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.STORE_COLD_PIPE: DataChannelGt(
        id="16a5738a-ce84-4f1e-9163-2afed31d866a",
        name=OcName.STORE_COLD_PIPE,
        display_name="Store Cold Pipe (C x 1000)",
        about_node_name=ON.STORE_COLD_PIPE,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.STORE_HOT_PIPE: DataChannelGt(
        id="8626fc06-72a4-4add-a782-0857ed569c8f",
        name=OcName.STORE_HOT_PIPE,
        display_name="Store Hot Pipe (C x 1000)",
        about_node_name=ON.STORE_HOT_PIPE,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[1].depth1: DataChannelGt(
        id="0f9d342c-510c-416a-9b35-336d76bfa100",
        name=OcName.TANK[1].depth1,
        display_name="Tank 1 Depth 1 (C x 1000)",
        about_node_name=ON.TEMP.TANK[1].depth1,
        captured_by_node_name=ON.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[1].depth2: DataChannelGt(
        id="b93ce968-a3cb-4ff9-b14d-d8ebc7ca84b1",
        name=OcName.TANK[1].depth2,
        display_name="Tank 1 Depth 2 (C x 1000)",
        about_node_name=ON.TEMP.TANK[1].depth2,
        captured_by_node_name=ON.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[1].depth3: DataChannelGt(
        id="a6d8e6af-85ff-4b6a-a50e-b2c6ed9225a2",
        name=OcName.TANK[1].depth3,
        display_name="Tank 1 Depth 3 (C x 1000)",
        about_node_name=ON.TEMP.TANK[1].depth3,
        captured_by_node_name=ON.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[1].depth4: DataChannelGt(
        id="c75ff5fd-67a2-45e3-a385-d3a7177e52ef",
        name=OcName.TANK[1].depth4,
        display_name="Tank 1 Depth 4 (C x 1000)",
        about_node_name=ON.TEMP.TANK[1].depth4,
        captured_by_node_name=ON.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.TANK[2].depth1: DataChannelGt(
        id="6b47a99a-270f-4138-b789-d327c020a005",
        name=OcName.TANK[2].depth1,
        display_name="Tank 2 Depth 1 (C x 1000)",
        about_node_name=ON.TEMP.TANK[2].depth1,
        captured_by_node_name=ON.TANK2_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[2].depth2: DataChannelGt(
        id="cf7fbae5-3925-4fc4-a9f0-a214e13f4a78",
        name=OcName.TANK[2].depth2,
        display_name="Tank 2 Depth 2 (C x 1000)",
        about_node_name=ON.TEMP.TANK[2].depth2,
        captured_by_node_name=ON.TANK2_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[2].depth3: DataChannelGt(
        id="4c74cbe0-376f-4eb8-a9f8-10f867cc9ddc",
        name=OcName.TANK[2].depth3,
        display_name="Tank 2 Depth 3 (C x 1000)",
        about_node_name=ON.TEMP.TANK[2].depth3,
        captured_by_node_name=ON.TANK2_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[2].depth4: DataChannelGt(
        id="5ae83637-89be-4277-b751-370d980f3420",
        name=OcName.TANK[2].depth4,
        display_name="Tank 2 Depth 4 (C x 1000)",
        about_node_name=ON.TEMP.TANK[2].depth4,
        captured_by_node_name=ON.TANK2_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[3].depth1: DataChannelGt(
        id="181d2d1b-8295-43cb-bc5e-8311fdfbcead",
        name=OcName.TANK[3].depth1,
        display_name="Tank 3 Depth 1 (C x 1000)",
        about_node_name=ON.TEMP.TANK[3].depth1,
        captured_by_node_name=ON.TANK3_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[3].depth2: DataChannelGt(
        id="37bd0b6b-0369-4c6a-be3e-eb707bf1ecc2",
        name=OcName.TANK[3].depth2,
        display_name="Tank 3 Depth 2 (C x 1000)",
        about_node_name=ON.TEMP.TANK[3].depth2,
        captured_by_node_name=ON.TANK3_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[3].depth3: DataChannelGt(
        id="653aaaa1-d351-4ab6-8b12-05bc6892c7ad",
        name=OcName.TANK[3].depth3,
        display_name="Tank 3 Depth 3 (C x 1000)",
        about_node_name=ON.TEMP.TANK[3].depth3,
        captured_by_node_name=ON.TANK3_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.TANK[3].depth4: DataChannelGt(
        id="89765322-2847-4e47-8c3c-216edac77897",
        name=OcName.TANK[3].depth4,
        display_name="Tank 3 Depth 4 (C x 1000)",
        about_node_name=ON.TEMP.TANK[3].depth4,
        captured_by_node_name=ON.TANK3_READER,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OcName.OAT: DataChannelGt(
        id="49db0f92-1c25-46c0-b154-4f71923ce969",
        name=OcName.OAT,
        display_name="Outside Air Temp (C x 1000)",
        about_node_name=ON.TEMP.OAT,
        captured_by_node_name=ON.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    # OcName.HP_FOSSIL_LWT:
    # # Non-essential temperatures
    # DataChannelGt(
    #     id="87f1e9f5-8959-4780-9195-0f1267822e22",
    #     name=OcName.HP_FOSSIL_LWT,
    #     display_name="HeatPump Fossil LWT(C x 1000)",
    #     about_node_name=ON.HP_FOSSIL_LWT,
    #     captured_by_node_name=ON.ANALOG_TEMP,
    #     telemetry_name=TelemetryName.WaterTempCTimes1000,
    #     terminal_asset_alias=OAK_TA,
    # ),
    # Integrated Flow
    OcName.DIST_FLOW_INTEGRATED: DataChannelGt(
        id="f28b814a-0579-4c9f-b08e-5e81e077dd1d",
        name=OcName.DIST_FLOW_INTEGRATED,
        display_name="Distribution Gallons x 100",
        about_node_name=ON.DIST_FLOW,
        captured_by_node_name=ON.DIST_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.PRIMARY_FLOW_INTEGRATED: DataChannelGt(
        id="94c3ab5c-7dd1-43c5-9870-733930251396",
        name=OcName.PRIMARY_FLOW_INTEGRATED,
        display_name="Primary Gallons x 100",
        about_node_name=ON.PRIMARY_FLOW,
        captured_by_node_name=ON.PRIMARY_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
    OcName.STORE_FLOW_INTEGRATED: DataChannelGt(
        id="10fbb233-9987-4b5f-8b13-0f38fcff73b4",
        name=OcName.STORE_FLOW_INTEGRATED,
        display_name="Store Gallons x 100",
        about_node_name=ON.STORE_FLOW,
        captured_by_node_name=ON.STORE_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
}


OakAliasMapper = AliasMapper(scada="oak")
OakAliasMapper.channel_mappings = {}