from typing import Dict, List


class TankTempName:
    def __init__(self, tank_prefix: str):
        self.tank_prefix = tank_prefix

    @property
    def depth1(self) -> str:
        return f"{self.tank_prefix}-depth1"

    @property
    def depth2(self) -> str:
        return f"{self.tank_prefix}-depth2"

    @property
    def depth3(self) -> str:
        return f"{self.tank_prefix}-depth3"

    @property
    def depth4(self) -> str:
        return f"{self.tank_prefix}-depth4"
    

class ZoneName:
    def __init__(self, zone:str, idx:int):
        zone_name = f"zone{idx+1}-{zone}".lower()
        self.NAME = zone_name
        self.TEMP = f"{zone_name}-temp"
        self.SET = f"{zone_name}-set"
        self.STATE = f"{zone_name}-state"
        self.STAT = f"{zone_name}-stat"
        self.GW_TEMP = f"{zone_name}-gw-temp"


class House0TempName:
    TANK: Dict[int, TankTempName]
    ZONE: Dict[str, ZoneName]
    ZONE_NAME: List[str]
    ZONE_SET: List[str]
    ZONE_STAT: List[str]
    OAT = "oat"
    BUFFER_DEPTH1 = "buffer-depth1"
    BUFFER_DEPTH2 = "buffer-depth2"
    BUFFER_DEPTH3 = "buffer-depth3"
    BUFFER_DEPTH4 = "buffer-depth4"

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        self.TANK = {}
        for i in range(total_store_tanks):
            self.TANK[i+1] = TankTempName(tank_prefix=f"tank{i+1}")

        self.ZONE = {}
        for i in range(len(zone_list)):
            self.ZONE[zone_list[i]] = ZoneName(zone=zone_list[i], idx=i)

class House0Names:
    SCADA = "s"
    HOME_ALONE = "h"
    PRIMARY_POWER_METER = "primary-power-meter"
    HP_IDU = "hp-idu"
    HP_ODU = "hp-odu"
    PRIMARY_PUMP = "primary-pump"
    STORE_PUMP = "store-pump"
    HP_LWT = "hp-lwt"
    HP_EWT = "hp-ewt"
    DIST_SWT = "dist-swt"
    DIST_RWT = "dist-rwt"
    STORE_HOT_PIPE = "store-hot-pipe"
    STORE_COLD_PIPE = "store-cold-pipe"
    BUFFER_HOT_PIPE = "buffer-hot-pipe"
    BUFFER_COLD_PIPE = "buffer-cold-pipe"
    TEMP: House0TempName
    DIST_FLOW = "dist-flow"
    PRIMARY_FLOW = "primary-flow"
    STORE_FLOW = "store-flow"

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        self.TEMP = House0TempName(
            total_store_tanks=total_store_tanks, zone_list=zone_list
        )





class House0ChannelNames:

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
    TANK: Dict[int, TankTempName]
    ZONE: Dict[str, ZoneName]

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

    # Misc Temperature Channels
    HP_FOSSIL_LWT = "hp-fossil-lwt"
    OIL_BOILER_FLOW_INTEGRATED = "oil-boiler-flow"
    BUFFER_WELL_TEMP = "buffer-well"
    AMPHA_DIST_SWT = "ampha-dist-swt"
    AMPHB_DIST_SWT = "amphb-dist-swt"

    def __init__(self, total_store_tanks, zone_list):
        self.ZONE = {}
        for zone in zone_list:
            self.ZONE[zone] = ZoneName(zone, zone_list.index(zone))
        
        self.TANK = {}
        for i in range(total_store_tanks):
            self.TANK[i+1] = TankTempName(tank_prefix=f"tank{i+1}")
            