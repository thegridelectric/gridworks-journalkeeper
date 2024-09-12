import dotenv
import pendulum
from gjk.config import Settings
from gjk.journal_keeper_hack import JournalKeeperHack
from gjk.utils import str_from_ms

day_offset = 0
days = 1

install_s  = pendulum.datetime(2023, 11, 13, 0, 0 , 0, tz='America/New_York').int_timestamp

atn_alias = "hw1.isone.me.versant.keene.beech"
#install_s = pendulum.datetime(2024, 4, 18, 1, 50, 0, tz="America/New_York").int_timestamp

# 11-13 through 2023-11-29 00:00:00.163
start_s = day_offset * 3600 * 24 + install_s


duration_hrs = days * 24 + 1

print(str_from_ms(start_s * 1000))
p = JournalKeeperHack(Settings(_env_file=dotenv.find_dotenv()))

p.load_messages_from_s3(start_s, duration_hrs, "beech")
