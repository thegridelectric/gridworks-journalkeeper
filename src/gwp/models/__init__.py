""" List of all the models """

from src.gwp.models.message import Message
from src.gwp.models.message import MessageSql
from src.gwp.models.scada import Scada
from src.gwp.models.scada import ScadaSql


__all__ = [
    "Message",
    "MessageSql",
    "Scada",
    "ScadaSql",
]
