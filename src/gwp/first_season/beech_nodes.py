from gwp.first_season.house_0 import House0Names


class BeechNodes:
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

    # Power/Current Nodes
    DIST_PUMP = "dist-pump"
    HP_IDU = "hp-idu"
    HP_ODU = "hp-odu"
    OIL_BOILER = "oil-boiler"
    PRIMARY_PUMP = "primary-pump"
    STORE_PUMP = "store-pump"
    ELT_1 = "elt1"

    # Thermostat Zones
    DOWN_ZONE = "down-zone"
    UP_ZONE = "up-zone"

    # Misc
    ELT1_PWR = "elt1-pwr"
    HP_FOSSIL_LWT = "hp-fossil-lwt"

    # Reading nodes
    ANALOG_TEMP = "analog-temp"
    BUFFER_TANK_READER = "buffer-tank-reader"
    TANK1_READER = "tank1-reader"
    TANK2_READER = "tank1-reader"
    TANK3_READER = "tank1-reader"
    TANK4_READER = "tank1-reader"
