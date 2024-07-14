from pydantic import BaseModel

class TerminalAssetHack(BaseModel):
    g_node_id: str
    g_node_alias: str
    short_alias: str
    type_name: str
    message_persisted_ms: int
    file_name: str
