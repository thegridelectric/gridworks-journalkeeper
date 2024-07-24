import json

from gw.errors import GwTypeError

from gwp.types.base_asl_types import TypeMakerByName
from gwp.types.heartbeat_a import HeartbeatA


def get_tuple_from_type(msg_bytes: bytes) -> HeartbeatA:
    """
    Given the serialized content of a message, returns the associated
    GridWorks tuple.

    Raises: GwTypeError  If the payload does not
    """
    content = json.loads(msg_bytes.decode("utf-8"))
    if "TypeName" not in content.keys():
        raise GwTypeError(f"No TypeName - so not a type. Keys: <{content.keys()}>")
    outer_type_name = content["TypeName"]

    # Andrew puts all his messages in a wrapper of tn 'gw'
    # which must have a 'Payload'.
    if outer_type_name == "gw":
        if "Payload" not in content.keys():
            raise GwTypeError(f"Type Gw must include Payload! Keys: <{content.keys()}>")
        content = content["Payload"]

    Codec = TypeMakerByName[content["TypeName"]]
    return Codec.dict_to_tuple(content)
