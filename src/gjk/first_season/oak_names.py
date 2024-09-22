from gjk.first_season.house_0 import DEFAULT_ANALOG_READER, H0C, H0N

OAK_TA = "hw1.isone.me.versant.keene.oak.ta"


OAK_ZONE_1 = "living-rm"
OAK_ZONE_2 = "garage"
OAK_ZONE_3 = "gear-rm"
OAK_ZONE_4 = "upstairs"
OAK_ZONE_LIST = [OAK_ZONE_1, OAK_ZONE_2, OAK_ZONE_3, OAK_ZONE_4]


class OakNames(H0N):
    buffer_well = "buffer-well"
    analog_temp_reader = DEFAULT_ANALOG_READER
    oil_boiler = "oil-boiler"
    house_panel = "house-panel"
    hp_fossil_lwt = "hp-fossil-lwt"


class OakChannelNames(H0C):
    buffer_well_temp = "buffer-well"
    zone1_gw_temp = "zone1-living-rm-gw-temp"
    oil_boiler_pwr = "oil-boiler-pwr"
    hp_fossil_lwt = "hp-fossil-lwt"
    house_panel_pwr = "house-panel-pwr"


ON = OakNames(total_store_tanks=3, zone_list=OAK_ZONE_LIST)
OC = OakChannelNames(total_store_tanks=3, zone_list=OAK_ZONE_LIST)
