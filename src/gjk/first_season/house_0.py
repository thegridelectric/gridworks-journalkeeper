from typing import Dict, List, Literal


class TankTempName:
    def __init__(self, tank_prefix: str):
        self.tank_prefix = tank_prefix

    @property
    def DEPTH_1(self) -> str:
        return f"{self.tank_prefix}-depth1"

    @property
    def DEPTH_2(self) -> str:
        return f"{self.tank_prefix}-depth2"

    @property
    def DEPTH_3(self) -> str:
        return f"{self.tank_prefix}-depth3"

    @property
    def DEPTH_4(self) -> str:
        return f"{self.tank_prefix}-depth4"


class House0TempName:
    TANK: Dict[int, TankTempName]
    ZONE_LIST: List[str]
    OAT = "oat"
    BUFFER_DEPTH_1 = "buffer-depth1"
    BUFFER_DEPTH_2 = "buffer-depth2"
    BUFFER_DEPTH_3 = "buffer-depth3"
    BUFFER_DEPTH_4 = "buffer-depth4"

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        self.TANK = {}
        for i in range(total_store_tanks):
            self.TANK[i + 1] = TankTempName(tank_prefix=f"tank{i + 1}")

        self.ZONE_LIST = []
        for i in range(len(zone_list)):
            self.ZONE_LIST.append(f"zone{i + 1}-{zone_list[i]}".lower())


class House0Names:
    SCADA: Literal["s"] = "s"
    HOME_ALONE: Literal["h"] = "h"
    REV_GRADE_POWER_METER = "power-meter"
    HP_IDU: Literal["hp-idu"] = "hp-idu"
    HP_ODU: Literal["hp-odu"] = "hp-odu"
    PRIMARY_PUMP: Literal["primary-pump"] = "primary-pump"
    STORE_PUMP: Literal["store-pump"] = "store-pump"
    DIST_PUMP: Literal["dist-pump"] = "dist-pump"
    HP_LW = "hp-lw"
    HP_EW = "hp-ew"
    DIST_SW = "dist-sw"
    DIST_RW = "dist-rw"
    STORE_HOT_PIPE = "store-hot-pipe"
    STORE_COLD_PIPE = "store-cold-pipe"
    BUFFER_HOT_PIPE = "buffer-hot-pipe"
    BUFFER_COLD_PIPE = "buffer-cold-pipe"
    ISO_VALVE = "iso-valve"
    ISO_VALVE_RELAY = "iso-valve-relay"
    CHARGE_DISCHARGE_VALVE = "chg-dschg-valve"
    CHARGE_DISCHARGE_VALVE_RELAY = "chg-dschg-valve-relay"
    HP_FAILSAFE_RELAY = "hp-failsafe-relay"
    HP_SCADA_OPS_RELAY = "hp-scada-ops-relay"
    HP_DHW_V_HEAT_RELAY = "hp-dhw-v-heat-relay"
    AQUASTAT_CTRL_RELAY = "aquastat-ctrl-relay"
    TEMP: House0TempName
    DIST_FLOW = "dist-flow"
    PRIMARY_FLOW = "primary-flow"
    STORE_FLOW = "store-flow"

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        self.TEMP = House0TempName(
            total_store_tanks=total_store_tanks, zone_list=zone_list
        )
