import dotenv
import pendulum
from gjk.config import Settings
from gjk.journal_keeper_hack import JournalKeeperHack
from gjk.utils import str_from_ms

day_offset = 0
days = 1 / 24

atn_alias = "hw1.isone.me.versant.keene.oak"

install_s = pendulum.datetime(2023, 12, 1, 0, 0, 0, tz="America/New_York").int_timestamp

start_s = day_offset * 3600 * 24 + install_s
duration_hrs = days * 24 + 1
print(str_from_ms(start_s * 1000))

p = JournalKeeperHack(Settings(_env_file=dotenv.find_dotenv()), alias="oak")
p.load_messages_from_s3(start_s, duration_hrs, "oak")
