""" List of all the models """

from src.gwp.models.message import Message, MessageSql
from src.gwp.models.scada import Scada, ScadaSql

__all__ = [
    "Message",
    "MessageSql",
    "Scada",
    "ScadaSql",
    ]