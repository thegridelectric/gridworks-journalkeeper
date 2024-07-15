from typing import Dict

import dotenv

from gwp.config import Settings


BEECH_ID = "19ee09df-80ba-437b-b6c1-1eebe9d34801"
OAK_ID = "a61ede79-4efd-4dbc-af14-a99b002d5ce5"

SCADA_DICT: Dict = {
    BEECH_ID: "hw1.isone.me.versant.keene.beech.scada",
    OAK_ID: "hw1.isone.me.versant.keene.oak.scada",
}


def check_scada(id: str, alias: str):
    if id not in SCADA_DICT.keys() and alias not in SCADA_DICT.values():
        raise Exception(f"New pair <{id}, {alias}>")
    elif id not in SCADA_DICT.keys() and alias in SCADA_DICT.values():
        raise Exception(f"Wrong id <{id}> for <{alias}>.")
    elif id in SCADA_DICT.keys():
        if SCADA_DICT[id] != alias:
            raise Exception(f"Wrong id <{id}> for <{alias}>")
