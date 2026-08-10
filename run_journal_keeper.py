# Service entrypoint — systemd ExecStart (see service/journalkeeper.service).
import dotenv

from gjk.config import Settings
from gjk.journal_keeper import JournalKeeper
from gjk.sema import SemaCodec

dotenv.load_dotenv(dotenv.find_dotenv())

jk = JournalKeeper(settings=Settings(), codec=SemaCodec())
jk.start()
# start() is non-blocking (daemon consumer thread); hold the process open.
jk.consuming_thread.join()
