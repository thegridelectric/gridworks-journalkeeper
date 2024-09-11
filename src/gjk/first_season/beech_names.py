BEECH_TA = "hw1.isone.me.versant.keene.beech.ta"

class BN:
    """
    This class provides the names of the Beech Spaceheat Nodes.
    These are immutable identifiers of the Spaceheat Nodes associated
    to the Beech SCADA GNode ("hw1.isone.me.versant.keene.beech.scada")
    """

    # Temperature Nodes
    BUFFER_COLD_PIPE = "buffer-cold-pipe"
    BUFFER_HOT_PIPE = "buffer-hot-pipe"
    BUFFER_DEPTH1 = "buffer-depth1"
    BUFFER_DEPTH2 = "buffer-depth2"
    BUFFER_DEPTH3 = "buffer-depth3"
    BUFFER_DEPTH4 = "buffer-depth4"
    BUFFER_WELL = "buffer-well"
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

    # Relay Nodes
    AQUASTAT_CTRL_RELAY = "aquastat-ctrl-relay"
    CHG_DSCHG_VALVE_RELAY = "chg-dschg-valve-relay"
    HP_FAILSAFE_RELAY = "hp-failsafe-relay"
    HP_SCADA_OPS_RELAY = "hp-scada-ops-relay"
    ISO_VALVE_RELAY = "iso-valve-relay"

    # Flow Nodes
    DIST_FLOW = "dist-flow"
    PRIMARY_FLOW = "primary-flow"
    STORE_FLOW = "store-flow"
    OIL_BOILER_FLOW = "oil-boiler-flow"

    # Power/Current Nodes
    DIST_PUMP = "dist-pump"
    HP_IDU = "hp-idu"
    HP_ODU = "hp-odu"
    OIL_BOILER = "oil-boiler"
    PRIMARY_PUMP = "primary-pump"
    STORE_PUMP = "store-pump"
    ELT_1 = "elt1"

    # Thermostat Zone Related

    # actors for reading the thermostats
    DOWN_ZONE_STAT = "zone1-down-stat"
    UP_ZONE_STAT = "zone2-up-stat"

    # passive nodes
    DOWN_ZONE = "zone1-down"
    DOWN_ZONE_SET = "zone1-down-set"

    UP_ZONE = "zone2-up"
    UP_ZONE_SET = "zone2-up-set"

    # Misc
    ELT1_PWR = "elt1-pwr"
    HP_FOSSIL_LWT = "hp-fossil-lwt"
    AMPHA_DIST_SWT = "ampha-dist-swt"
    AMPHB_DIST_SWT = "amphb-dist-swt"

    # Reading nodes
    ANALOG_TEMP = "analog-temp"
    BUFFER_TANK_READER = "buffer"
    TANK1_READER = "tank1"
    TANK2_READER = "tank2"
    TANK3_READER = "tank3"
    TANK4_READER = "tank4"
    POWER_METER = "power-meter"


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
    DOWN_ZONE_TEMP = f"{BN.DOWN_ZONE}-temp"
    DOWN_ZONE_SET = BN.DOWN_ZONE_SET
    DOWN_ZONE_STATE = f"{BN.DOWN_ZONE}-state"
    UP_ZONE_TEMP = f"{BN.UP_ZONE}-temp"
    UP_ZONE_SET = BN.UP_ZONE_SET
    UP_ZONE_STATE = f"{BN.UP_ZONE}-state"

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
    DOWN_ZONE_GW_TEMP = f"{BN.DOWN_ZONE}-gw-temp"
    UP_ZONE_GW_TEMP = f"{BN.UP_ZONE}-gw-temp"
    HP_FOSSIL_LWT = "hp-fossil-lwt"
    OIL_BOILER_FLOW_INTEGRATED = "oil-boiler-flow"
    BUFFER_WELL_TEMP = "buffer-well"
    AMPHA_DIST_SWT = "ampha-dist-swt"
    AMPHB_DIST_SWT = "amphb-dist-swt"
