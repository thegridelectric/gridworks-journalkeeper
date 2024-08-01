import json
from typing import Dict
from typing import List

import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk.config import Settings
from gjk.enums import TelemetryName
from gjk.first_season.alias_mapper import AliasMapper
from gjk.first_season.beech_nodes import BeechNodes as BN
from gjk.models import bulk_insert_idempotent
from gjk.types import DataChannelGt


class BcName:
    """
    This class provides the names of the beech channels, which
    are local (within Beech) immutable identifiers.

    A channel is a tuple of [AboutNode,  CapturedByNode, TelemetryName]
    where AboutNode and CapturedByNode are Spaceheat Nodes.
    """

    # Temperature Channels
    BUFFER_COLD_PIPE = "buffer-cold-pipe"
    BUFFER_HOT_PIPE = "buffer-hot-pipe"
    BUFFER_WELL_TEMP = "buffer-well"
    BUFFER_DEPTH1_TEMP = "buffer-depth1"
    BUFFER_DEPTH2_TEMP = "buffer-depth2"
    BUFFER_DEPTH3_TEMP = "buffer-depth3"
    BUFFER_DEPTH4_TEMP = "buffer-depth4"
    DIST_RWT = "dist-rwt"
    DIST_SWT = "dist-swt"
    HP_EWT = "hp-ewt"
    HP_LWT = "hp-lwt"
    OAT = "oat"
    STORE_COLD_PIPE = "store-cold-pipe"
    STORE_HOT_PIPE = "store-hot-pipe"
    TANK1_DEPTH1 = "tank1-depth1"
    TANK1_DEPTH2 = "tank1-depth2"
    TANK1_DEPTH3 = "tank1-depth3"
    TANK1_DEPTH4 = "tank1-depth4"
    TANK2_DEPTH1 = "tank2-depth1"
    TANK2_DEPTH2 = "tank2-depth2"
    TANK2_DEPTH3 = "tank2-depth3"
    TANK2_DEPTH4 = "tank2-depth4"
    TANK3_DEPTH1 = "tank3-depth1"
    TANK3_DEPTH2 = "tank3-depth2"
    TANK3_DEPTH3 = "tank3-depth3"
    TANK3_DEPTH4 = "tank3-depth4"
    DOWN_ZONE_TEMP = "down-zone-temp"
    DOWN_ZONE_SET = "down-zone-set"
    UP_ZONE_TEMP = "up-zone-temp"
    UP_ZONE_SET = "up-zone-set"

    # Relay Energization Channels
    AQUASTAT_CTRL_RELAY_ENERGIZATION = "aquastat-ctrl-relay-energization"
    CHG_DSCHG_VALVE_RELAY_ENERGIZATION = "chg-dschg-valve-relay-energization"
    HP_FAILSAFE_RELAY_ENERGIZATION = "hp-failsafe-relay-energization"
    HP_SCADA_OPS_RELAY_ENERGIZATION = "hp-scada-ops-relay-energization"
    ISO_VALVE_RELAY_ENERGIZATION = "iso-valve-relay-energization"

    # Flow Channels
    DIST_FLOW_INTEGRATED = "dist-flow-integrated"
    PRIMARY_FLOW_INTEGRATED = "primary-flow-integrated"
    STORE_FLOW_INTEGRATED = "store-flow-integrated"

    # Power Channels
    DIST_PUMP_PWR = "dist-pump-pwr"
    HP_IDU_PWR = "hp-idu-pwr"
    HP_ODU_PWR = "hp-odu-pwr"
    OIL_BOILER_PWR = "oil-boiler-pwr"
    PRIMARY_PUMP_PWR = "primary-pump-pwr"
    STORE_PUMP_PWR = "store-pump-pwr"

    # Misc Channels
    # Misc Temperature Channels
    DOWN_ZONE_GW_TEMP = "down-zone-gw-temp"
    UP_ZONE_GW_TEMP = "up-zone-gw-temp"
    HP_FOSSIL_LWT = "hp-fossil-lwt"
    OIL_BOILER_FLOW_INTEGRATED = "oil-boiler-flow"
    BUFFER_WELL_TEMP = "buffer-well-temp"
    AMPHA_DIST_SWT = "ampha-dist-swt"
    AMPHB_DIST_SWT = "amphb-dist-swt"


# def hyph_to_upper(word: str) -> str:
#     return word.replace("-", "_").upper()


def load_channels():
    settings = Settings(_env_file=dotenv.find_dotenv())
    engine = create_engine(settings.db_url.get_secret_value())
    Session = sessionmaker(bind=engine)
    session = Session()
    beech_channel_sqls = list(
        map(lambda x: x.as_sql(), BEECH_CHANNELS_BY_NAME.values())
    )
    bulk_insert_idempotent(session, beech_channel_sqls)


BEECH_CHANNELS_BY_NAME: Dict[str, DataChannelGt] = {
    BcName.STORE_PUMP_PWR: DataChannelGt(
        id="ac35c2a9-e317-45e8-a036-52fa5cbd8380",
        name=BcName.STORE_PUMP_PWR,
        display_name="Store pump power",
        about_node_name=BN.STORE_PUMP,
        captured_by_node_name=BN.POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        start_s=1701293980,  # 2023-11-29 16:39:40 America/New_York
    ),
    BcName.PRIMARY_PUMP_PWR: DataChannelGt(
        id="1e3c34e3-1e83-4dae-bfe3-a698c4618b5a",
        name=BcName.PRIMARY_PUMP_PWR,
        display_name="Primary pump power",
        about_node_name=BN.PRIMARY_PUMP,
        captured_by_node_name=BN.POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        start_s=1701293980,  # 2023-11-29 16:39:40 America/New_York
    ),
    BcName.DIST_PUMP_PWR: DataChannelGt(
        id="a2ebe9fa-05ba-4665-a6ba-dbc85aee530c",
        name=BcName.DIST_PUMP_PWR,
        display_name="Distribution pump power",
        about_node_name=BN.DIST_PUMP,
        captured_by_node_name=BN.POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        start_s=1701293980,  # 2023-11-29 16:39:40 America/New_York
    ),
    BcName.AMPHA_DIST_SWT: DataChannelGt(
        id="38e95a83-270c-4520-af1a-b85a07a3c02f",
        name=BcName.AMPHA_DIST_SWT,
        display_name="Dist SWT measured with an AmphA",
        about_node_name=BN.AMPHA_DIST_SWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1704862800,  # 2024-01-10
    ),
    BcName.AMPHB_DIST_SWT: DataChannelGt(
        id="934c04d3-2a06-475d-a708-5129979ceedf",
        name=BcName.AMPHB_DIST_SWT,
        display_name="Dist SWT measured with an Amphb",
        about_node_name=BN.AMPHB_DIST_SWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1704862800,  # 2024-01-10
    ),
    BcName.HP_ODU_PWR: DataChannelGt(
        id="498da855-bac5-47e9-b83a-a11e56a50e67",
        name=BcName.HP_ODU_PWR,
        display_name="HP ODU Power",
        about_node_name=BN.HP_ODU,
        captured_by_node_name=BN.POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        start_s=1704862800,  # 2024-01-10
    ),
    BcName.HP_IDU_PWR: DataChannelGt(
        id="beabac86-7caa-4ab4-a50b-af1ad54ed165",
        name=BcName.HP_IDU_PWR,
        display_name="HP IDU Power",
        about_node_name=BN.HP_IDU,
        captured_by_node_name=BN.POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        start_s=1704862800,  # 2024-01-10
    ),
    BcName.BUFFER_WELL_TEMP: DataChannelGt(
        id="8120ae8d-0029-4c85-bca1-9a70235bf423",
        name=BcName.BUFFER_WELL_TEMP,
        display_name="Buffer Well Temp",
        about_node_name=BN.BUFFER_WELL,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1706763600,  # 2024-02-01
    ),
    BcName.OIL_BOILER_FLOW_INTEGRATED: DataChannelGt(
        id="251871dd-6dc8-40d9-a811-f62319461435",
        name=BcName.OIL_BOILER_FLOW_INTEGRATED,
        display_name="Oil Boiler Integrated Flow",
        about_node_name=BN.OIL_BOILER_FLOW,
        captured_by_node_name=BN.OIL_BOILER_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        start_s=1706763600,  # 2024-02-01
    ),
    BcName.DOWN_ZONE_SET: DataChannelGt(
        id="dd4c0d78-d2e0-490c-b064-2f33b85ec431",
        name=BcName.DOWN_ZONE_SET,
        display_name="Down Zone Honeywell Setpoint",
        about_node_name=BN.DOWN_ZONE,
        captured_by_node_name=BN.DOWN_ZONE,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        start_s=1700683960,  # 2023-11-22 15:12:40.000 America/NY
    ),
    BcName.DOWN_ZONE_TEMP: DataChannelGt(
        id="0334a75a-48ee-4da1-8b77-96fe05b0c3db",
        name=BcName.DOWN_ZONE_TEMP,
        display_name="Down Zone Honeywell Temp",
        about_node_name=BN.DOWN_ZONE,
        captured_by_node_name=BN.DOWN_ZONE,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        start_s=1700683960,  # 2023-11-22 15:12:40.000 America/NY
    ),
    BcName.UP_ZONE_SET: DataChannelGt(
        id="581f758b-632f-426a-aebc-7432c416a99e",
        name=BcName.UP_ZONE_SET,
        display_name="Up Zone Honeywell Setpoint",
        about_node_name=BN.UP_ZONE,
        captured_by_node_name=BN.UP_ZONE,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        start_s=1700683960,  # 2023-11-22 15:12:40.000 America/NY
    ),
    BcName.UP_ZONE_TEMP: DataChannelGt(
        id="2196a6b7-90d1-42d0-b3f0-748f393bb35a",
        name=BcName.UP_ZONE_TEMP,
        display_name="Up Zone Honeywell Temp",
        about_node_name=BN.UP_ZONE,
        captured_by_node_name=BN.UP_ZONE,
        telemetry_name=TelemetryName.AirTempFTimes1000,
        start_s=1700683960,  # 2023-11-22 15:12:40.000 America/NY
    ),
    BcName.OIL_BOILER_PWR: DataChannelGt(
        id="83fe770f-e022-4ad6-a471-cfb83e1b64be",
        name=BcName.OIL_BOILER_PWR,
        display_name="Oil Boiler pump power",
        about_node_name=BN.OIL_BOILER,
        captured_by_node_name=BN.POWER_METER,
        telemetry_name=TelemetryName.PowerW,
        start_s=1700590500,  # 2023-11-21 13:15:00.000 America/NY
    ),
    BcName.BUFFER_COLD_PIPE: DataChannelGt(
        id="a47abb1a-06fc-4d9b-a548-8531c482d3f2",
        name=BcName.BUFFER_COLD_PIPE,
        display_name="Buffer Cold (C x 1000)",
        about_node_name=BN.BUFFER_COLD_PIPE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.BUFFER_HOT_PIPE: DataChannelGt(
        id="cb542708-ba47-4c8b-9261-029dae126d6f",
        name=BcName.BUFFER_HOT_PIPE,
        display_name="Buffer Hot (C x 1000)",
        about_node_name=BN.BUFFER_HOT_PIPE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.BUFFER_DEPTH1_TEMP: DataChannelGt(
        id="17c338be-f09f-40c0-b99b-3a8d11076a1e",
        name=BcName.BUFFER_DEPTH1_TEMP,
        display_name="Buffer Depth 1 (C x 1000)",
        about_node_name=BN.BUFFER_DEPTH1,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.BUFFER_DEPTH2_TEMP: DataChannelGt(
        id="064e5051-f724-4c65-b28f-d890afd7b3e4",
        name=BcName.BUFFER_DEPTH2_TEMP,
        display_name="Buffer Depth 2 (C x 1000)",
        about_node_name=BN.BUFFER_DEPTH2,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.BUFFER_DEPTH3_TEMP: DataChannelGt(
        id="15ef5472-9530-4e91-b8c6-6434101fc113",
        name=BcName.BUFFER_DEPTH3_TEMP,
        display_name="Buffer Depth 3 (C x 1000)",
        about_node_name=BN.BUFFER_DEPTH3,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.BUFFER_DEPTH4_TEMP: DataChannelGt(
        id="44a834d9-8052-4f21-9512-3b2579ba8491",
        name=BcName.BUFFER_DEPTH4_TEMP,
        display_name="Buffer Depth 4 (C x 1000)",
        about_node_name=BN.BUFFER_DEPTH4,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.BUFFER_WELL_TEMP: DataChannelGt(
        id="f908be82-f8ac-42e7-8203-7057eeef79a8",
        name=BcName.BUFFER_WELL_TEMP,
        display_name="Buffer Well (C x 1000)",
        about_node_name=BN.BUFFER_WELL,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.DIST_RWT: DataChannelGt(
        id="2fe25fbf-400a-418e-b2dc-35e3b62f8250",
        name=BcName.DIST_RWT,
        display_name="Dist RWT (C x 1000)",
        about_node_name=BN.DIST_RWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.DIST_SWT: DataChannelGt(
        id="5dae9382-a2b1-4f11-9259-3f3f026944ab",
        name=BcName.DIST_SWT,
        display_name="Dist SWT (C x 1000)",
        about_node_name=BN.DIST_SWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.UP_ZONE_GW_TEMP: DataChannelGt(
        id="0d9c3cac-5813-4881-a0f7-35d90ac4bd49",
        name=BcName.UP_ZONE_GW_TEMP,
        display_name="Upstairs Zone Temp (C x 1000)",
        about_node_name=BN.UP_ZONE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        start_s=1708221240,  # 2024-02-17 20:54:00 America/NY
    ),
    BcName.DOWN_ZONE_GW_TEMP: DataChannelGt(
        id="01af1b8d-d22a-47c6-8e25-421be9df09b6",
        name=BcName.DOWN_ZONE_GW_TEMP,
        display_name="Downstairs Zone Temp (C x 1000)",
        about_node_name=BN.DOWN_ZONE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        start_s=1700006400,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.HP_EWT: DataChannelGt(
        id="cecc9b94-9b4b-45ce-a8e9-4c63d24530aa",
        name=BcName.HP_EWT,
        display_name="HP EWT (C x 1000)",
        about_node_name=BN.HP_EWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.HP_LWT: DataChannelGt(
        id="a49db047-e38f-44a4-b773-29102c2fc526",
        name=BcName.HP_LWT,
        display_name="HP EWT (C x 1000)",
        about_node_name=BN.HP_LWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.STORE_COLD_PIPE: DataChannelGt(
        id="16a5738a-ce84-4f1e-9163-2afed31d866a",
        name=BcName.STORE_COLD_PIPE,
        display_name="Store Cold Pipe (C x 1000)",
        about_node_name=BN.STORE_COLD_PIPE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.STORE_HOT_PIPE: DataChannelGt(
        id="8626fc06-72a4-4add-a782-0857ed569c8f",
        name=BcName.STORE_HOT_PIPE,
        display_name="Store Hot Pipe (C x 1000)",
        about_node_name=BN.STORE_HOT_PIPE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.TANK1_DEPTH1: DataChannelGt(
        id="0f9d342c-510c-416a-9b35-336d76bfa100",
        name=BcName.TANK1_DEPTH1,
        display_name="Tank 1 Depth 1 (C x 1000)",
        about_node_name=BN.TANK1_DEPTH1,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.TANK1_DEPTH2: DataChannelGt(
        id="b93ce968-a3cb-4ff9-b14d-d8ebc7ca84b1",
        name=BcName.TANK1_DEPTH2,
        display_name="Tank 1 Depth 2 (C x 1000)",
        about_node_name=BN.TANK1_DEPTH2,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.TANK1_DEPTH3: DataChannelGt(
        id="a6d8e6af-85ff-4b6a-a50e-b2c6ed9225a2",
        name=BcName.TANK1_DEPTH3,
        display_name="Tank 1 Depth 3 (C x 1000)",
        about_node_name=BN.TANK1_DEPTH3,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.TANK1_DEPTH4: DataChannelGt(
        id="c75ff5fd-67a2-45e3-a385-d3a7177e52ef",
        name=BcName.TANK1_DEPTH4,
        display_name="Tank 1 Depth 4 (C x 1000)",
        about_node_name=BN.TANK1_DEPTH4,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.TANK2_DEPTH1: DataChannelGt(
        id="6b47a99a-270f-4138-b789-d327c020a005",
        name=BcName.TANK2_DEPTH1,
        display_name="Tank 2 Depth 1 (C x 1000)",
        about_node_name=BN.TANK2_DEPTH1,
        captured_by_node_name=BN.TANK2_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.TANK2_DEPTH2: DataChannelGt(
        id="cf7fbae5-3925-4fc4-a9f0-a214e13f4a78",
        name=BcName.TANK2_DEPTH2,
        display_name="Tank 2 Depth 2 (C x 1000)",
        about_node_name=BN.TANK2_DEPTH2,
        captured_by_node_name=BN.TANK2_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.TANK2_DEPTH3: DataChannelGt(
        id="4c74cbe0-376f-4eb8-a9f8-10f867cc9ddc",
        name=BcName.TANK2_DEPTH3,
        display_name="Tank 2 Depth 3 (C x 1000)",
        about_node_name=BN.TANK2_DEPTH3,
        captured_by_node_name=BN.TANK2_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.TANK2_DEPTH4: DataChannelGt(
        id="5ae83637-89be-4277-b751-370d980f3420",
        name=BcName.TANK2_DEPTH4,
        display_name="Tank 2 Depth 4 (C x 1000)",
        about_node_name=BN.TANK2_DEPTH4,
        captured_by_node_name=BN.TANK2_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.TANK3_DEPTH1: DataChannelGt(
        id="181d2d1b-8295-43cb-bc5e-8311fdfbcead",
        name=BcName.TANK3_DEPTH1,
        display_name="Tank 3 Depth 1 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH1,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.TANK3_DEPTH2: DataChannelGt(
        id="37bd0b6b-0369-4c6a-be3e-eb707bf1ecc2",
        name=BcName.TANK3_DEPTH2,
        display_name="Tank 3 Depth 2 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH2,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.TANK3_DEPTH3: DataChannelGt(
        id="653aaaa1-d351-4ab6-8b12-05bc6892c7ad",
        name=BcName.TANK3_DEPTH3,
        display_name="Tank 3 Depth 3 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH3,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.TANK3_DEPTH4: DataChannelGt(
        id="89765322-2847-4e47-8c3c-216edac77897",
        name=BcName.TANK3_DEPTH4,
        display_name="Tank 3 Depth 4 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH4,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    BcName.OAT: DataChannelGt(
        id="49db0f92-1c25-46c0-b154-4f71923ce969",
        name=BcName.OAT,
        display_name="Outside Air Temp (C x 1000)",
        about_node_name=BN.OAT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.AirTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.HP_FOSSIL_LWT:
    # Non-essential temperatures
    DataChannelGt(
        id="87f1e9f5-8959-4780-9195-0f1267822e22",
        name=BcName.HP_FOSSIL_LWT,
        display_name="HeatPump Fossil LWT(C x 1000)",
        about_node_name=BN.HP_FOSSIL_LWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    # Integrated Flow
    BcName.DIST_FLOW_INTEGRATED: DataChannelGt(
        id="f28b814a-0579-4c9f-b08e-5e81e077dd1d",
        name=BcName.DIST_FLOW_INTEGRATED,
        display_name="Distribution Gallons x 100",
        about_node_name=BN.DIST_FLOW,
        captured_by_node_name=BN.DIST_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.PRIMARY_FLOW_INTEGRATED: DataChannelGt(
        id="94c3ab5c-7dd1-43c5-9870-733930251396",
        name=BcName.PRIMARY_FLOW_INTEGRATED,
        display_name="Primary Gallons x 100",
        about_node_name=BN.PRIMARY_FLOW,
        captured_by_node_name=BN.PRIMARY_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
    BcName.STORE_FLOW_INTEGRATED: DataChannelGt(
        id="10fbb233-9987-4b5f-8b13-0f38fcff73b4",
        name=BcName.STORE_FLOW_INTEGRATED,
        display_name="Store Gallons x 100",
        about_node_name=BN.STORE_FLOW,
        captured_by_node_name=BN.STORE_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
        start_s=1699885800,  # 2023 Nov 13, 09:35 America/NY
    ),
}


BeechAliasMapper = AliasMapper(scada="beech")

BeechAliasMapper.channel_mappings = {
    BcName.BUFFER_COLD_PIPE: [
        (1699885800, "a.buffer.cold.pipe.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.BUFFER_HOT_PIPE: [
        (1699885800, "a.buffer.hot.pipe.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.DIST_FLOW_INTEGRATED: [
        (1699885800, "a.dist.flow"),  # 2023-11-13 09:35 America/NY
        (1706293200, "dist.flow"),  # 2024-01-26 13:20:00.000 America/NY
    ],
    BcName.DIST_SWT: [
        (1699885800, "a.dist.swt.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.DIST_RWT: [
        (1699885800, "a.dist.rwt.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.HP_EWT: [
        (1699885800, "a.hp.ewt.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.HP_FOSSIL_LWT: [
        (1699885800, "a.hp.fossil.lwt.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.HP_LWT: [
        (1699885800, "a.hp.lwt.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.PRIMARY_FLOW_INTEGRATED: [
        (1699885800, "a.primary.flow"),  # 2023-11-13 09:35 America/NY
        (1706388600, "heatpump.flow"),  # 2024-01-27 15:50 America/NY
    ],
    BcName.OAT: [
        (1699885800, "a.outdoor.air.temp"),  # 2023-11-13 09:35 America/NY
        (1700002650, "oat"),  # 2023-11-14 17:57:30.000 America/NY
        (1700020500, "a.outdoor.air.temp"),  # 2023-11-14 22:55:00.000 America/NY
    ],
    BcName.STORE_COLD_PIPE: [
        (1699885800, "a.store.cold.pipe.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.STORE_FLOW_INTEGRATED: [
        (1699885800, "a.store.flow"),  # 2023-11-13 09:35 America/NY
        (1706805390, "store.discharge.flow") # 2024-02-01 11:36:30 America/NY
    ],
    BcName.STORE_HOT_PIPE: [
        (1699885800, "a.store.hot.pipe.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.TANK1_DEPTH1: [
        (1699885800, "a.tank1.temp.depth1"),  # 2023-11-13 09:35 America/NY
        (1707343260, "tank1.temp.depth1"), # 2024-02-07 17:01:00 America/NY
    ],
    BcName.TANK1_DEPTH2: [
        (1699885800, "a.tank1.temp.depth2"),  # 2023-11-13 09:35 America/NY
        (1707343260, "tank1.temp.depth2"),  # 2024-02-07 17:01:00 America/NY
    ],
    BcName.TANK1_DEPTH3: [
        (1699885800, "a.tank1.temp.depth3"),  # 2023-11-13 09:35 America/NY
        (1707343260, "tank1.temp.depth3"),  # 2024-02-07 17:01:00 America/NY
    ],
    BcName.TANK1_DEPTH4: [
        (1699885800, "a.tank1.temp.depth4"),  # 2023-11-13 09:35 America/NY
        (1707343260, "tank1.temp.depth4"),  # 2024-02-07 17:01:00 America/NY
    ],
    BcName.OIL_BOILER_PWR: [
        (1700590500, "oilboiler"),  # 2023-11-21 13:15 America/NY,
        (1701293980, "a.m.oil.boiler.power") # 2023-11-29 16:39:40 America/New_York
    ],
    BcName.DOWN_ZONE_TEMP: [
        (1700683960, "a.thermostat.downstairs.temp"),  # 2023-11-22 15:12:40 America/NY
    ],
    BcName.DOWN_ZONE_SET: [
        (1700683960, "a.thermostat.downstairs.set"),  # 2023-11-22 15:12:40 America/NY
    ],
    BcName.UP_ZONE_TEMP: [
        (1700683960, "a.thermostat.upstairs.temp"),  # 2023-11-22 15:12:40 America/NY
    ],
    BcName.UP_ZONE_SET: [
        (1700683960, "a.thermostat.upstairs.set"),  # 2023-11-22 15:12:40 America/NY
    ],
    BcName.OIL_BOILER_FLOW_INTEGRATED: [
        (1706194440, "oilboiler.flow"),  # 2024-01-25 09:54:00 America/NY
    ],
    BcName.BUFFER_WELL_TEMP: [
        (1706211900, "buffer.well.temp"),  # 2024-01-25 14:45:00 America/NY
    ],
    BcName.BUFFER_DEPTH1_TEMP: [
        (1706194440, "buffer.temp.depth1"),  # 2024-01-25 09:54:00 America/NY
    ],
    BcName.BUFFER_DEPTH2_TEMP: [
        (1706194440, "buffer.temp.depth2"),  # 2024-01-25 09:54:00 America/NY
    ],
    BcName.BUFFER_DEPTH3_TEMP: [
        (1706194440, "buffer.temp.depth3"),  # 2024-01-25 09:54:00 America/NY
    ],
    BcName.BUFFER_DEPTH4_TEMP: [
        (1706194440, "buffer.temp.depth4"),  # 2024-01-25 09:54:00 America/NY
    ],
    BcName.HP_ODU_PWR: [
        (1701293980, "a.m.hp.outdoor.power"),  # 2023-11-29 16:39:40 America/New_York
    ],
    BcName.HP_IDU_PWR: [
        (1701293980, "a.m.hp.indoor.power"),  # 2024-02-01 America/NY
    ],
    BcName.AMPHA_DIST_SWT: [
        (1704117000, "ampha.distfwt"),  #  2024-01-01 08:50:00.000 America/New_York
    ],
    BcName.AMPHB_DIST_SWT: [
        (1704117000, "amphb.distfwt") # 2024-01-01 08:50:00.000 America/New_York
    ],
    BcName.DIST_PUMP_PWR: [
        (1701293980, "a.m.dist.pump.power"),  # 2023-11-29 16:39:40 America/New_York
    ],
    BcName.PRIMARY_PUMP_PWR: [
        (1701293980, "a.m.primary.pump.power"),  # 2023-11-29 16:39:40 America/New_York
        (1707430530, "primary.pump.power"),  # 2024-02-08 17:15:30 America/NY
    ],
    BcName.STORE_PUMP_PWR: [
        (1701293980, "a.m.store.pump.power"),  # 2023-11-29 16:39:40 America/New_York
    ],
    BcName.TANK2_DEPTH1: [
        (1707480930, "tank2.temp.depth1"), # 2024-02-09 07:15:30 America/NY
    ],
    BcName.TANK2_DEPTH2: [
        (1707480930, "tank2.temp.depth2"), # 2024-02-09 07:15:30 America/NY
    ],
    BcName.TANK2_DEPTH3: [
        (1707480930, "tank2.temp.depth3"), # 2024-02-09 07:15:30 America/NY
    ],
    BcName.TANK2_DEPTH4: [
        (1707480930, "tank2.temp.depth4"), # 2024-02-09 07:15:30 America/NY
    ],
    BcName.TANK3_DEPTH1: [
        (1707494220, "tank3.temp.depth1"), # 2024-02-09 10:57:00 America/NY
    ],
    BcName.TANK3_DEPTH2: [
        (1707494220, "tank3.temp.depth2"), # 2024-02-09 10:57:00 America/NY
    ],
    BcName.TANK3_DEPTH3: [
        (1707494220, "tank3.temp.depth3"), # 2024-02-09 10:57:00 America/NY
    ],
    BcName.TANK3_DEPTH4: [
        (1707494220, "tank3.temp.depth4"), # 2024-02-09 10:57:00 America/NY
    ],
    BcName.DOWN_ZONE_GW_TEMP: [
        (1700006400, "statcheck"),  # 2023-11-13 09:35 America/NY
        (1706194440, "stat1check"),  # 2024-01-25 09:54:00 America/NY
        (1708265130, "stat1.temp"), # 2024-02-18 09:05:30 America/NY
    ],
    BcName.UP_ZONE_GW_TEMP: [
        (1708221240, "stat.up.check"), # 2024-02-17 20:54:00 America/NY
         (1708265130, "stat2.temp"), # 2024-02-18 09:05:30 America/NY
    ],
}

