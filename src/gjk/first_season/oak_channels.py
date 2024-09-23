from typing import Dict, List, Optional

from deepdiff import DeepDiff
from gjk.codec import pyd_to_sql
from gjk.enums import TelemetryName
from gjk.first_season.alias_mapper import AliasMapper
from gjk.first_season.oak_names import OAK_TA, OAK_ZONE_1, OAK_ZONE_2, OC, ON
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

    dcs = {
        dc
        for dc in session.query(DataChannelSql).all()
        if "oak" in dc.terminal_asset_alias
    }

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
    OC.store_pump_pwr: DataChannelGt(
        id="b4d40404-dc8f-4353-9cd6-3eea4457eae9",
        name=OC.store_pump_pwr,
        display_name="Store pump power",
        about_node_name=ON.store_pump,
        captured_by_node_name=ON.primary_power_meter,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OC.primary_pump_pwr: DataChannelGt(
        id="55173ca8-ac64-424a-9b74-652c60971826",
        name=OC.primary_pump_pwr,
        display_name="Primary pump power",
        about_node_name=ON.primary_pump,
        captured_by_node_name=ON.primary_power_meter,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OC.dist_pump_pwr: DataChannelGt(
        id="aeace76a-ff0a-49d8-8643-426e6890cafd",
        name=OC.dist_pump_pwr,
        display_name="Distribution pump power",
        about_node_name=ON.dist_pump,
        captured_by_node_name=ON.dist_pump,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OC.hp_odu_pwr: DataChannelGt(
        id="299a47c4-9d2a-45f7-9b68-60334742853e",
        name=OC.hp_odu_pwr,
        display_name="HP ODU Power",
        about_node_name=ON.hp_odu,
        captured_by_node_name=ON.primary_power_meter,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
        in_power_metering=True,
    ),
    OC.hp_idu_pwr: DataChannelGt(
        id="b2a8d472-c4f1-4476-8524-3a24782a4c7e",
        name=OC.hp_idu_pwr,
        display_name="HP IDU Power",
        about_node_name=ON.hp_idu,
        captured_by_node_name=ON.primary_power_meter,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
        in_power_metering=True,
    ),
    OC.buffer_well_temp: DataChannelGt(
        id="ba620238-63c6-4e38-903e-3e2755b8a779",
        name=OC.buffer_well_temp,
        display_name="Buffer Well Temp",
        about_node_name=ON.buffer_well,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.zone[OAK_ZONE_1].set: DataChannelGt(
        id="42177a16-edea-41e0-bbcb-b200d762af5d",
        name=OC.zone[OAK_ZONE_1].set,
        display_name="Living room Zone Honeywell Setpoint",
        about_node_name=ON.zone[OAK_ZONE_1].stat,
        captured_by_node_name=ON.zone[OAK_ZONE_1].stat,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.zone[OAK_ZONE_1].temp: DataChannelGt(
        id="f316b3c4-3f9c-4d8a-a862-7074aeda1f86",
        name=OC.zone[OAK_ZONE_1].temp,
        display_name="Living room Zone Honeywell Temp",
        about_node_name=ON.zone[OAK_ZONE_1].zone_name,
        captured_by_node_name=ON.zone[OAK_ZONE_1].stat,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.zone[OAK_ZONE_2].set: DataChannelGt(
        id="4b5b5534-39a9-4424-b79a-b1611438283d",
        name=OC.zone[OAK_ZONE_2].set,
        display_name="Garage Zone Honeywell Setpoint",
        about_node_name=ON.zone[OAK_ZONE_2].stat,
        captured_by_node_name=ON.zone[OAK_ZONE_2].stat,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.zone[OAK_ZONE_2].temp: DataChannelGt(
        id="971a2c41-a459-4857-a9c0-ad3b6b2eb5dc",
        name=OC.zone[OAK_ZONE_2].temp,
        display_name="Garage Zone Honeywell Temp",
        about_node_name=ON.zone[OAK_ZONE_2].zone_name,
        captured_by_node_name=ON.zone[OAK_ZONE_2].stat,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.oil_boiler_pwr: DataChannelGt(
        id="960beace-27fd-4038-8579-74b0afe6f578",
        name=OC.oil_boiler_pwr,
        display_name="Oil Boiler pump power",
        about_node_name=ON.oil_boiler,
        captured_by_node_name=ON.primary_power_meter,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
    OC.buffer_cold_pipe: DataChannelGt(
        id="9eb57c30-7339-4c08-8fc1-0f7371f09a58",
        name=OC.buffer_cold_pipe,
        display_name="Buffer Cold (C x 1000)",
        about_node_name=ON.buffer_cold_pipe,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.buffer_hot_pipe: DataChannelGt(
        id="d9d6ff80-3da1-4b71-8630-32d4b6020b43",
        name=OC.buffer_hot_pipe,
        display_name="Buffer Hot (C x 1000)",
        about_node_name=ON.buffer_hot_pipe,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.buffer.depth1: DataChannelGt(
        id="21936d6b-869b-4dc1-b501-20c76782589f",
        name=OC.buffer.depth1,
        display_name="Buffer Depth 1 (C x 1000)",
        about_node_name=OC.buffer.depth1,
        captured_by_node_name=ON.buffer.reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.buffer.depth2: DataChannelGt(
        id="f5a0c2ce-7e8f-4efa-842e-81a7e15a5196",
        name=OC.buffer.depth2,
        display_name="Buffer Depth 2 (C x 1000)",
        about_node_name=OC.buffer.depth2,
        captured_by_node_name=ON.buffer.reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.buffer.depth3: DataChannelGt(
        id="79c30451-cfaf-409d-9b74-78a3e6619f0c",
        name=OC.buffer.depth3,
        display_name="Buffer Depth 3 (C x 1000)",
        about_node_name=OC.buffer.depth3,
        captured_by_node_name=ON.buffer.reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.buffer.depth4: DataChannelGt(
        id="ad86f200-f4b5-4eae-b987-6e925efae172",
        name=OC.buffer.depth4,
        display_name="Buffer Depth 4 (C x 1000)",
        about_node_name=OC.buffer.depth4,
        captured_by_node_name=ON.buffer.reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.buffer_well_temp: DataChannelGt(
        id="aedfa460-849f-4297-8428-13ba10e99f9e",
        name=OC.buffer_well_temp,
        display_name="Buffer Well (C x 1000)",
        about_node_name=ON.buffer_well,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.dist_rwt: DataChannelGt(
        id="5df1a8dd-f5dc-496c-928b-f4e98553005d",
        name=OC.dist_rwt,
        display_name="Dist RWT (C x 1000)",
        about_node_name=ON.dist_rwt,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.dist_swt: DataChannelGt(
        id="6eb54a9d-50d3-4854-b388-3b635813edd5",
        name=OC.dist_swt,
        display_name="Dist SWT (C x 1000)",
        about_node_name=ON.dist_swt,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.zone1_gw_temp: DataChannelGt(
        id="3eca0062-4885-4687-b29a-d6a1af8f777a",
        name=OC.zone1_gw_temp,
        display_name="Living room Zone Temp (C x 1000) measured by Gw",
        about_node_name=ON.zone[OAK_ZONE_1].zone_name,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.hp_ewt: DataChannelGt(
        id="7c9d7fe3-2e16-45e6-ab5d-2ee9468dbd71",
        name=OC.hp_ewt,
        display_name="HP EWT (C x 1000)",
        about_node_name=ON.hp_ewt,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.hp_lwt: DataChannelGt(
        id="8d55e3f6-13eb-4297-9618-9ac08f1e575b",
        name=OC.hp_lwt,
        display_name="HP EWT (C x 1000)",
        about_node_name=ON.hp_lwt,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.store_cold_pipe: DataChannelGt(
        id="3d9d5b42-d03a-4b3a-9697-edc7d8a21faf",
        name=OC.store_cold_pipe,
        display_name="Store Cold Pipe (C x 1000)",
        about_node_name=ON.store_cold_pipe,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.store_hot_pipe: DataChannelGt(
        id="bdb37789-b64e-44cc-aeb9-e277909709c5",
        name=OC.store_hot_pipe,
        display_name="Store Hot Pipe (C x 1000)",
        about_node_name=ON.store_hot_pipe,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.tank[1].depth1: DataChannelGt(
        id="a795290b-4743-4aed-8431-cee0b17c64c3",
        name=OC.tank[1].depth1,
        display_name="Tank 1 Depth 1 (C x 1000)",
        about_node_name=ON.tank[1].depth1,
        captured_by_node_name=ON.tank[1].reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.tank[1].depth2: DataChannelGt(
        id="f7e93847-5d0b-42f9-9f9e-ca6d918904a1",
        name=OC.tank[1].depth2,
        display_name="Tank 1 Depth 2 (C x 1000)",
        about_node_name=ON.tank[1].depth2,
        captured_by_node_name=ON.tank[1].reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.tank[1].depth3: DataChannelGt(
        id="bf793144-60b3-46c9-8389-d40bae6698a0",
        name=OC.tank[1].depth3,
        display_name="Tank 1 Depth 3 (C x 1000)",
        about_node_name=ON.tank[1].depth3,
        captured_by_node_name=ON.tank[1].reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.tank[1].depth4: DataChannelGt(
        id="90b0336c-562c-471c-bba3-4849b5177aa5",
        name=OC.tank[1].depth4,
        display_name="Tank 1 Depth 4 (C x 1000)",
        about_node_name=ON.tank[1].depth4,
        captured_by_node_name=ON.tank[1].reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.tank[2].depth1: DataChannelGt(
        id="b93ded06-9ba3-41d9-ac88-cd9363c19cdf",
        name=OC.tank[2].depth1,
        display_name="Tank 2 Depth 1 (C x 1000)",
        about_node_name=ON.tank[2].depth1,
        captured_by_node_name=ON.tank[2].reader,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OC.tank[2].depth2: DataChannelGt(
        id="ac471b36-790f-4f0d-b1b0-70ed038a266f",
        name=OC.tank[2].depth2,
        display_name="Tank 2 Depth 2 (C x 1000)",
        about_node_name=ON.tank[2].depth2,
        captured_by_node_name=ON.tank[2].reader,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OC.tank[2].depth3: DataChannelGt(
        id="6c9e22d8-8a54-42d9-858e-7d83a7665ca4",
        name=OC.tank[2].depth3,
        display_name="Tank 2 Depth 3 (C x 1000)",
        about_node_name=ON.tank[2].depth3,
        captured_by_node_name=ON.tank[2].reader,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OC.tank[2].depth4: DataChannelGt(
        id="f1f5202a-2eff-434f-84d7-71ee0773036e",
        name=OC.tank[2].depth4,
        display_name="Tank 2 Depth 4 (C x 1000)",
        about_node_name=ON.tank[2].depth4,
        captured_by_node_name=ON.tank[2].reader,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OC.tank[3].depth1: DataChannelGt(
        id="cf5e185c-c6e7-4e67-80ea-d423dc226dfb",
        name=OC.tank[3].depth1,
        display_name="Tank 3 Depth 1 (C x 1000)",
        about_node_name=ON.tank[3].depth1,
        captured_by_node_name=ON.tank[3].reader,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OC.tank[3].depth2: DataChannelGt(
        id="e104bee6-abde-4004-9f60-563bed779c94",
        name=OC.tank[3].depth2,
        display_name="Tank 3 Depth 2 (C x 1000)",
        about_node_name=ON.tank[3].depth2,
        captured_by_node_name=ON.tank[3].reader,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OC.tank[3].depth3: DataChannelGt(
        id="099aa9c1-97a5-4e61-bce1-81933b5096d6",
        name=OC.tank[3].depth3,
        display_name="Tank 3 Depth 3 (C x 1000)",
        about_node_name=ON.tank[3].depth3,
        captured_by_node_name=ON.tank[3].reader,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OC.tank[3].depth4: DataChannelGt(
        id="5a2abdd5-9295-4ea5-a83c-1e8188e3f382",
        name=OC.tank[3].depth4,
        display_name="Tank 3 Depth 4 (C x 1000)",
        about_node_name=ON.tank[3].depth4,
        captured_by_node_name=ON.tank[3].reader,
        terminal_asset_alias=OAK_TA,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    OC.oat: DataChannelGt(
        id="b3cb7460-cf74-40b3-afd0-42a5e236ba0b",
        name=OC.oat,
        display_name="Outside Air Temp (C x 1000)",
        about_node_name=ON.oat,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    OC.hp_fossil_lwt: DataChannelGt(
        id="a5e82dbd-7956-4d5d-926d-2c1db9bec7e2",
        name=OC.hp_fossil_lwt,
        display_name="HeatPump Fossil LWT(C x 1000)",
        about_node_name=ON.hp_fossil_lwt,
        captured_by_node_name=ON.analog_temp_reader,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        terminal_asset_alias=OAK_TA,
    ),
    # Integrated Flow
    OC.dist_flow_integrated: DataChannelGt(
        id="648fcb3a-80b6-4886-9567-af6197021ce9",
        name=OC.dist_flow_integrated,
        display_name="Distribution Gallons x 100",
        about_node_name=ON.dist_flow,
        captured_by_node_name=ON.dist_flow,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
    OC.primary_flow_integrated: DataChannelGt(
        id="1a8d2419-4704-46aa-b7ee-27d148e6a07e",
        name=OC.primary_flow_integrated,
        display_name="Primary Gallons x 100",
        about_node_name=ON.primary_flow,
        captured_by_node_name=ON.primary_flow,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
    OC.store_flow_integrated: DataChannelGt(
        id="b52dc84b-47c5-477b-8a65-eb60b62b5948",
        name=OC.store_flow_integrated,
        display_name="Store Gallons x 100",
        about_node_name=ON.store_flow,
        captured_by_node_name=ON.store_flow,
        telemetry_name=TelemetryName.GallonsTimes100,
        terminal_asset_alias=OAK_TA,
    ),
    OC.house_panel_pwr: DataChannelGt(
        id="69a485b0-6e60-4eae-b417-0c787ae35cd4",
        name=OC.house_panel_pwr,
        display_name="House Panel Power",
        about_node_name=ON.house_panel,
        captured_by_node_name=ON.house_panel,
        telemetry_name=TelemetryName.PowerW,
        terminal_asset_alias=OAK_TA,
    ),
}


OakAliasMapper = AliasMapper(scada="oak")
OakAliasMapper.channel_mappings = {
    OC.primary_flow_integrated: [
        (1701406790, "a.primary.flow"),
    ],
    OC.store_flow_integrated: [
        (1701406790, "a.store.flow"),
    ],
    OC.hp_lwt: [
        (1701406790, "a.hp.lwt.temp"),
    ],
    OC.hp_ewt: [
        (1701406790, "a.hp.ewt.temp"),
    ],
    OC.store_hot_pipe: [
        (1701406790, "a.store.hot.pipe.temp"),
    ],
    OC.store_cold_pipe: [
        (1701406790, "a.store.cold.pipe.temp"),
    ],
    OC.buffer_hot_pipe: [
        (1701406790, "a.buffer.hot.pipe.temp"),
    ],
    OC.buffer_cold_pipe: [
        (1701406790, "a.buffer.cold.pipe.temp"),
    ],
    OC.hp_fossil_lwt: [
        (1701406790, "a.hp.fossil.lwt.temp"),
    ],
    OC.oat: [(1701406790, "a.oat.temp")],
    OC.zone1_gw_temp: [
        (1701406790, "statcheck"),
    ],
    OC.oil_boiler_pwr: [
        (1701406800, "a.m.oil.boiler.power"),
    ],
    OC.dist_swt: [
        (1701406800, "a.dist.swt.temp"),
    ],
    OC.dist_rwt: [
        (1701406800, "a.dist.rwt.temp"),
    ],
    OC.dist_flow_integrated: [
        (1701406810, "a.dist.flow"),
    ],
    OC.zone[OAK_ZONE_1].temp: [
        (1701406840, "a.thermostat.living.room.temp"),
    ],
    OC.zone[OAK_ZONE_1].set: [
        (1701406840, "a.thermostat.living.room.set"),
    ],
    OC.zone[OAK_ZONE_2].temp: [(1701406840, "a.thermostat.garage.temp")],
    OC.zone[OAK_ZONE_2].set: [(1701406840, "a.thermostat.garage.set")],
    OC.hp_odu_pwr: [(1701406870, "a.m.hp.outdoor.power")],
    OC.hp_idu_pwr: [(1701406870, "a.m.hp.indoor.power")],
    OC.dist_pump_pwr: [(1701406870, "a.m.dist.pump.power")],
    OC.primary_pump_pwr: [(1701406870, "a.m.primary.pump.power")],
    OC.store_pump_pwr: [(1701406870, "a.m.store.pump.power")],
    OC.house_panel_pwr: [(1701406900, "a.m.house.panel.power")],
}
