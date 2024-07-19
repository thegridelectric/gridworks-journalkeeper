import json
import os
import uuid
from typing import List

import dotenv
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from gwp.config import Settings
from gwp.enums import TelemetryName
from gwp.first_season.beech_nodes import BeechNodes as BN
from gwp.models import Message
from gwp.models import bulk_insert_dempotent
from gwp.types import DataChannelGt


class BeechChannels:
    """
    This class provides the names of the beech channels, which
    are local (within Beech) immutable identifiers.

    A channel is a tuple of [AboutNode,  CapturedByNode, TelemetryName]
    where AboutNode and CapturedByNode are Spaceheat Nodes.
    """

    # Temperature Channels
    BUFFER_COLD_PIPE_TEMP = "buffer-cold-pipe"
    BUFFER_HOT_PIPE_TEMP = "buffer-hot-pipe"
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
    # Misc Power Channels
    ELT1_PWR = "elt1-pwr"


def hyph_to_upper(word: str) -> str:
    return word.replace("-", "_").upper()


def print_channels():
    file_name = "beech_layout"
    msg_file = f"tests/sample_messages/{file_name}.json"
    with open(msg_file, "r") as file:
        content = json.load(file)
    channels = content["DataChannels"]
    channel_names = list(map(lambda x: x["Name"], channels))
    channel_names.sort()
    for name in channel_names:
        print(f'    {hyph_to_upper(name)} = "{name}"')


def populate_db_w_beech_channels():
    """
    Eventually, authority for making data channels will belong
    somewhere else (SCADA?). But this is the authority for
    beech
    """
    ...


from gwp.first_season.beech_channels import BeechChannels


channels: List[DataChannelGt] = [
    # Temperature Channels
    DataChannelGt(
        id="a47abb1a-06fc-4d9b-a548-8531c482d3f2",
        name=BeechChannels.BUFFER_COLD_PIPE_TEMP,
        display_name="Buffer Cold (C x 1000)",
        about_node_name=BN.BUFFER_COLD_PIPE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="cb542708-ba47-4c8b-9261-029dae126d6f",
        name=BeechChannels.BUFFER_HOT_PIPE_TEMP,
        display_name="Buffer Hot (C x 1000)",
        about_node_name=BN.BUFFER_HOT_PIPE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="17c338be-f09f-40c0-b99b-3a8d11076a1e",
        name=BeechChannels.BUFFER_DEPTH1_TEMP,
        display_name="Buffer Depth 1 (C x 1000)",
        about_node_name=BN.BUFFER_DEPTH1,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="064e5051-f724-4c65-b28f-d890afd7b3e4",
        name=BeechChannels.BUFFER_DEPTH2_TEMP,
        display_name="Buffer Depth 2 (C x 1000)",
        about_node_name=BN.BUFFER_DEPTH2,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="15ef5472-9530-4e91-b8c6-6434101fc113",
        name=BeechChannels.BUFFER_DEPTH3_TEMP,
        display_name="Buffer Depth 3 (C x 1000)",
        about_node_name=BN.BUFFER_DEPTH3,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="44a834d9-8052-4f21-9512-3b2579ba8491",
        name=BeechChannels.BUFFER_DEPTH4_TEMP,
        display_name="Buffer Depth 4 (C x 1000)",
        about_node_name=BN.BUFFER_DEPTH4,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="f908be82-f8ac-42e7-8203-7057eeef79a8",
        name=BeechChannels.BUFFER_WELL_TEMP,
        display_name="Buffer Well (C x 1000)",
        about_node_name=BN.BUFFER_WELL,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="2fe25fbf-400a-418e-b2dc-35e3b62f8250",
        name=BeechChannels.DIST_RWT,
        display_name="Dist RWT (C x 1000)",
        about_node_name=BN.DIST_RWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="5dae9382-a2b1-4f11-9259-3f3f026944ab",
        name=BeechChannels.DIST_SWT,
        display_name="Dist SWT (C x 1000)",
        about_node_name=BN.DIST_SWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="cecc9b94-9b4b-45ce-a8e9-4c63d24530aa",
        name=BeechChannels.HP_EWT,
        display_name="HP EWT (C x 1000)",
        about_node_name=BN.HP_EWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="a49db047-e38f-44a4-b773-29102c2fc526",
        name=BeechChannels.HP_LWT,
        display_name="HP EWT (C x 1000)",
        about_node_name=BN.HP_LWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="8db4cf07-0131-4402-8539-13da86a4078f",
        name=BeechChannels.DIST_SWT,
        display_name="Outside Air Temp ( x 1000)",
        about_node_name=BN.DIST_SWT,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="16a5738a-ce84-4f1e-9163-2afed31d866a",
        name=BeechChannels.STORE_COLD_PIPE,
        display_name="Store Cold Pipe (C x 1000)",
        about_node_name=BN.STORE_COLD_PIPE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="8626fc06-72a4-4add-a782-0857ed569c8f",
        name=BeechChannels.STORE_HOT_PIPE,
        display_name="Store Hot Pipe (C x 1000)",
        about_node_name=BN.STORE_HOT_PIPE,
        captured_by_node_name=BN.ANALOG_TEMP,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="0f9d342c-510c-416a-9b35-336d76bfa100",
        name=BeechChannels.TANK1_DEPTH1,
        display_name="Tank 1 Depth 1 (C x 1000)",
        about_node_name=BN.TANK1_DEPTH1,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="b93ce968-a3cb-4ff9-b14d-d8ebc7ca84b1",
        name=BeechChannels.TANK1_DEPTH2,
        display_name="Tank 1 Depth 2 (C x 1000)",
        about_node_name=BN.TANK1_DEPTH2,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="a6d8e6af-85ff-4b6a-a50e-b2c6ed9225a2",
        name=BeechChannels.TANK1_DEPTH3,
        display_name="Tank 1 Depth 3 (C x 1000)",
        about_node_name=BN.TANK1_DEPTH3,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="c75ff5fd-67a2-45e3-a385-d3a7177e52ef",
        name=BeechChannels.TANK1_DEPTH4,
        display_name="Tank 1 Depth 4 (C x 1000)",
        about_node_name=BN.TANK1_DEPTH4,
        captured_by_node_name=BN.TANK1_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="6b47a99a-270f-4138-b789-d327c020a005",
        name=BeechChannels.TANK2_DEPTH1,
        display_name="Tank 2 Depth 1 (C x 1000)",
        about_node_name=BN.TANK2_DEPTH1,
        captured_by_node_name=BN.TANK2_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="cf7fbae5-3925-4fc4-a9f0-a214e13f4a78",
        name=BeechChannels.TANK2_DEPTH2,
        display_name="Tank 2 Depth 2 (C x 1000)",
        about_node_name=BN.TANK2_DEPTH2,
        captured_by_node_name=BN.TANK2_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="4c74cbe0-376f-4eb8-a9f8-10f867cc9ddc",
        name=BeechChannels.TANK2_DEPTH3,
        display_name="Tank 2 Depth 3 (C x 1000)",
        about_node_name=BN.TANK2_DEPTH3,
        captured_by_node_name=BN.TANK2_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="5ae83637-89be-4277-b751-370d980f3420",
        name=BeechChannels.TANK2_DEPTH4,
        display_name="Tank 2 Depth 4 (C x 1000)",
        about_node_name=BN.TANK2_DEPTH4,
        captured_by_node_name=BN.TANK2_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="181d2d1b-8295-43cb-bc5e-8311fdfbcead",
        name=BeechChannels.TANK3_DEPTH1,
        display_name="Tank 3 Depth 1 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH1,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="37bd0b6b-0369-4c6a-be3e-eb707bf1ecc2",
        name=BeechChannels.TANK3_DEPTH2,
        display_name="Tank 3 Depth 2 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH2,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="653aaaa1-d351-4ab6-8b12-05bc6892c7ad",
        name=BeechChannels.TANK3_DEPTH3,
        display_name="Tank 3 Depth 3 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH3,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="89765322-2847-4e47-8c3c-216edac77897",
        name=BeechChannels.TANK3_DEPTH4,
        display_name="Tank 3 Depth 4 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH4,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    DataChannelGt(
        id="",
        name=BeechChannels.TANK3_DEPTH4,
        display_name="Tank 3 Depth 4 (C x 1000)",
        about_node_name=BN.TANK3_DEPTH4,
        captured_by_node_name=BN.TANK3_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ).as_sql(),
    # Integrated Flow
    DataChannelGt(
        id="f28b814a-0579-4c9f-b08e-5e81e077dd1d",
        name=BeechChannels.DIST_FLOW_INTEGRATED,
        display_name="Distribution Gallons x 100",
        about_node_name=BN.DIST_FLOW,
        captured_by_node_name=BN.DIST_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
    ).as_sql(),
    DataChannelGt(
        id="94c3ab5c-7dd1-43c5-9870-733930251396",
        name=BeechChannels.PRIMARY_FLOW_INTEGRATED,
        display_name="Primary Gallons x 100",
        about_node_name=BN.PRIMARY_FLOW,
        captured_by_node_name=BN.PRIMARY_FLOW,
        telemetry_name=TelemetryName.GallonsTimes100,
    ).as_sql(),
]


def load_channels():
    settings = Settings(_env_file=dotenv.find_dotenv())
    engine = create_engine(settings.db_url.get_secret_value())
    Session = sessionmaker(bind=engine)
    session = Session()
    bulk_insert_dempotent(session, data)


from sqlalchemy import inspect
from sqlalchemy import tuple_


pk_keys = inspect(channels[0]).mapper.primary_key

# Build a query to check for existing primary keys
pk_tuples = [tuple(getattr(obj, key.name) for key in pk_keys) for obj in channels]

# Build the filter condition
condition = tuple_(*pk_keys).in_(pk_tuples)

# Query existing primary keys
existing_pks = session.query(*pk_keys).filter(condition).all()

new_objects = [
    obj
    for obj in channels
    if tuple(getattr(obj, key.name) for key in pk_keys) not in existing_pks_set
]
