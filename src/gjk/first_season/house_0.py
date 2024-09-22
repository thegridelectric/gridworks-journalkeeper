from typing import Dict, List

from gjk.enums import TelemetryName
from gjk.property_format import (
    SpaceheatName,
)
from pydantic import BaseModel

DEFAULT_ANALOG_READER = "analog-temp"


class ZoneName:
    def __init__(self, zone: str, idx: int):
        zone_name = f"zone{idx + 1}-{zone}".lower()
        self.zone_name = zone_name
        self.stat = f"{zone_name}-stat"


class TankNodes:
    def __init__(self, tank_name: str):
        self.reader = tank_name
        self.depth1 = f"{tank_name}-depth1"
        self.depth2 = f"{tank_name}-depth2"
        self.depth3 = f"{tank_name}-depth3"
        self.depth4 = f"{tank_name}-depth4"


class ZoneChannelName:
    def __init__(self, zone: str, idx: int):
        zone_name = f"zone{idx + 1}-{zone}".lower()
        self.temp = f"{zone_name}-temp"
        self.set = f"{zone_name}-set"
        self.state = f"{zone_name}-state"


class ChannelStub(BaseModel):
    name: SpaceheatName
    about_node_name: SpaceheatName
    captured_by_node_name: SpaceheatName
    telemetry_name: TelemetryName


class H0N:
    # core actors
    scada = "s"
    home_alone = "h"
    primary_power_meter = "power-meter"

    # core temperatures
    buffer_cold_pipe = "buffer-cold-pipe"
    buffer_hot_pipe = "buffer-hot-pipe"
    buffer = TankNodes("buffer")
    dist_rwt = "dist-rwt"
    dist_swt = "dist-swt"
    hp_ewt = "hp-ewt"
    hp_lwt = "hp-lwt"
    oat = "oat"
    store_cold_pipe = "store-cold-pipe"
    store_hot_pipe = "store-hot-pipe"

    # core power-metered nodes
    hp_idu = "hp-idu"
    hp_odu = "hp-odu"
    dist_pump = "dist-pump"
    primary_pump = "primary-pump"
    store_pump = "store-pump"

    # core flow-metered nodes
    dist_flow = "dist-flow"
    primary_flow = "primary-flow"
    store_flow = "store-flow"

    zone: Dict[str, ZoneName] = {}
    tank: Dict[int, TankNodes] = {}

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        for i in range(total_store_tanks):
            self.tank[i + 1] = TankNodes(f"tank{i + 1}")
        for i in range(len(zone_list)):
            self.zone[zone_list[i]] = ZoneName(zone=zone_list[i], idx=i)


class H0C:
    buffer_cold_pipe = H0N.buffer_cold_pipe
    buffer_hot_pipe = H0N.buffer_hot_pipe
    buffer = H0N.buffer
    dist_rwt = H0N.dist_rwt
    dist_swt = H0N.dist_swt
    hp_ewt = H0N.hp_ewt
    hp_lwt = H0N.hp_lwt
    oat = H0N.oat
    store_cold_pipe = H0N.store_cold_pipe
    store_hot_pipe = H0N.store_hot_pipe

    # Flow Channels
    dist_flow_integrated = f"{H0N.dist_flow}-integrated"
    primary_flow_integrated = f"{H0N.primary_flow}-integrated"
    store_flow_integrated = f"{H0N.store_flow}-integrated"

    # Power Channels
    dist_pump_pwr = f"{H0N.dist_pump}-pwr"
    hp_idu_pwr = f"{H0N.hp_idu}-pwr"
    hp_odu_pwr = f"{H0N.hp_odu}-pwr"
    primary_pump_pwr = f"{H0N.primary_pump}-pwr"
    store_pump_pwr = f"{H0N.store_pump}-pwr"

    zone: Dict[str, ZoneChannelName] = {}
    tank: Dict[int, TankNodes] = {}

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        for i in range(total_store_tanks):
            self.tank[i + 1] = TankNodes(f"tank{i + 1}")
        for i in range(len(zone_list)):
            self.zone[zone_list[i]] = ZoneChannelName(zone=zone_list[i], idx=i)


ChannelStubByName: Dict[str, ChannelStub] = {
    H0C.buffer_cold_pipe: ChannelStub(
        name=H0C.buffer_cold_pipe,
        about_node_name=H0N.buffer_cold_pipe,
        captured_by_node_name=DEFAULT_ANALOG_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
    H0C.buffer_hot_pipe: ChannelStub(
        name=H0C.buffer_hot_pipe,
        about_node_name=H0N.buffer_cold_pipe,
        captured_by_node_name=DEFAULT_ANALOG_READER,
        telemetry_name=TelemetryName.WaterTempCTimes1000,
    ),
}
