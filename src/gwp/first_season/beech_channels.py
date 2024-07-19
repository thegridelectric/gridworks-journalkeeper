import json
from typing import Dict
from typing import List

import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gwp.config import Settings
from gwp.enums import TelemetryName
from gwp.first_season.alias_mapper import AliasMapper
from gwp.first_season.beech_nodes import BeechNodes as BN
from gwp.models import bulk_insert_idempotent
from gwp.types import DataChannelGt


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
    ],
    BcName.OAT: [
        (1699885800, "a.outdoor.air.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.STORE_COLD_PIPE: [
        (1699885800, "a.store.cold.pipe.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.STORE_FLOW_INTEGRATED: [
        (1699885800, "a.store.flow"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.STORE_HOT_PIPE: [
        (1699885800, "a.store.hot.pipe.temp"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.TANK1_DEPTH1: [
        (1699885800, "a.tank1.temp.depth1"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.TANK1_DEPTH2: [
        (1699885800, "a.tank1.temp.depth2"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.TANK1_DEPTH3: [
        (1699885800, "a.tank1.temp.depth3"),  # 2023-11-13 09:35 America/NY
    ],
    BcName.TANK1_DEPTH4: [
        (1699885800, "a.tank1.temp.depth4"),  # 2023-11-13 09:35 America/NY
    ],
}
