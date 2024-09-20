from gjk.first_season.house_0 import House0Names, House0ChannelNames

OAK_TA = "hw1.isone.me.versant.keene.oak.ta"

zones = ["down", "up"]

ON = House0Names(total_store_tanks=3, zone_list=zones)
ON.BUFFER_WELL = "buffer-well"

OcName = House0ChannelNames(total_store_tanks=3, zone_list=zones)
