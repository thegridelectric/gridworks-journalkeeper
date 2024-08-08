from typing import Dict

BEECH_G_NODE_ID = "19ee09df-80ba-437b-b6c1-1eebe9d34801"
OAK_G_NODE_ID = "a61ede79-4efd-4dbc-af14-a99b002d5ce5"

BEECH_GNI_ID = "98542a17-3180-4f2a-a929-6023f0e7a106"
OAK_GNI_ID = "2270cca1-1bb6-4c13-ae0d-0ce14575543b"

SCADA_GNI_DICT: Dict = {
    "hw1.isone.me.versant.keene.beech.scada": BEECH_GNI_ID,
    "hw1.isone.me.versant.keene.oak.scada": OAK_GNI_ID,
}


def gni_from_alias(g_node_alias: str) -> str:
    if g_node_alias not in SCADA_GNI_DICT.keys():
        raise Exception(f"Untracked GNode Alias {g_node_alias}")
    return SCADA_GNI_DICT[g_node_alias]


def ta_from_alias(g_node_alias: str) -> str:
    if g_node_alias not in SCADA_GNI_DICT.keys():
        raise Exception(f"Untracked GNode Alias {g_node_alias}")
    return ".".join(g_node_alias.split(".")[:-1]) + ".ta"
