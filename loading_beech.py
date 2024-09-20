import dotenv
import pendulum
from gjk.config import Settings
from gjk.journal_keeper_hack import JournalKeeperHack
from gjk.utils import str_from_ms

day_offset = 0
days = 10

atn_alias = "hw1.isone.me.versant.keene.beech"

# install_s  = pendulum.datetime(2023, 11, 13, 0, 0 , 0, tz='America/New_York').int_timestamp
install_s = pendulum.datetime(2024, 5, 3, 18, 0, 0, tz="America/New_York").int_timestamp

start_s = day_offset * 3600 * 24 + install_s
duration_hrs = days * 24 + 1
print(str_from_ms(start_s * 1000))

p = JournalKeeperHack(Settings(_env_file=dotenv.find_dotenv()), alias='beech')
p.load_messages_from_s3(start_s, duration_hrs, "beech")
