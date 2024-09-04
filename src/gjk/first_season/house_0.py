from typing import Dict, List, Literal, Optional


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

class House0TempName:
    TANK: Dict[int, TankTempName]
    ZONE_LIST: List[str]
    OAT = "oat"
    BUFFER_DEPTH1 = "buffer-depth1"
    BUFFER_DEPTH2 = "buffer-depth2"
    BUFFER_DEPTH3 = "buffer-depth3"
    BUFFER_DEPTH4 = "buffer-depth4"

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        self.TANK = {}
        for i in range(total_store_tanks):
            self.TANK[i + 1] = TankTempName(tank_prefix=f"tank{i + 1}")

        self.ZONE_LIST = []
        for i in range(len(zone_list)):
            self.ZONE_LIST.append(f"zone{i + 1}-{zone_list[i]}".lower())


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
    # # Relay Nodes
    # AQUASTAT_CTRL_RELAY = "aquastat-ctrl-relay"
    # CHG_DSCHG_VALVE_RELAY = "chg-dschg-valve-relay"
    # HP_FAILSAFE_RELAY = "hp-failsafe-relay"
    # HP_SCADA_OPS_RELAY = "hp-scada-ops-relay"
    # ISO_VALVE_RELAY = "iso-valve-relay"

    def __init__(self, total_store_tanks: int, zone_list: List[str]):
        self.TEMP = House0TempName(
            total_store_tanks=total_store_tanks, zone_list=zone_list
        )
