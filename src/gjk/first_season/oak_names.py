from gjk.first_season.house_0 import House0Names, House0ChannelNames

OAK_TA = "hw1.isone.me.versant.keene.oak.ta"

zones = ["down", "up", "living-room", "garage"]

ON = House0Names(total_store_tanks=3, zone_list=zones)
ON.BUFFER_WELL = "buffer-well"
ON.BUFFER_TANK_READER = "buffer"
ON.TANK1_READER = "tank1"
ON.TANK2_READER = "tank2"
ON.TANK3_READER = "tank3"
ON.ANALOG_TEMP = "analog-temp"
ON.DIST_RWT = "dist-rwt"
ON.DIST_SWT = "dist-swt"
ON.DIST_PUMP = "dist-pump"
ON.HP_FOSSIL_LWT = "hp-fossil-lwt"
ON.OIL_BOILER = "oil-boiler"
ON.HOUSE_PANEL = "house-panel"

OcName = House0ChannelNames(total_store_tanks=3, zone_list=zones)
OcName.HOUSE_PANEL_PWR = "house-panel-pwr"
