# Try out in repl
import dotenv
from gjk.config import Settings
from gjk.journal_keeper import JournalKeeper

dotenv.load_dotenv(dotenv.find_dotenv())

j = JournalKeeper(Settings())
j.settings.g_node_alias
# go to http://hw1-1.electricity.works:15672/#/queues 
# (password in 1pass)
# and look for the queue whose name matches the gnode alias
j.settings.rabbit.url.get_secret_value()

j.start()

# examine as messages come in