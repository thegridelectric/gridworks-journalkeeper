import json
from typing import Optional

from gw.errors import GwTypeError

from gjk.types.asl_types import TypeMakerByName
from gjk.types.heartbeat_a import HeartbeatA

type_list = list(TypeMakerByName.keys())


def deserialize(msg_bytes: bytes) -> Optional[HeartbeatA]:
    """
    Given an instance of the type (i.e., a serialized byte string for sending
    as a message), returns the appropriate instance of the associated pydantic
    BaseModel class. Returns None if the TypeName is not recogized

    Raises: GwTypeError if msg_bytes fails the type authentication

    Returns: Instance of associated Pydantic object, or None if the
    TypeName is not recognized
    """
    content = json.loads(msg_bytes.decode("utf-8"))
    if "TypeName" not in content.keys():
        raise GwTypeError(f"No TypeName - so not a type. Keys: <{content.keys()}>")
    outer_type_name = content["TypeName"]

    # Scada messages all come in a 'gw' incomplete type

    # which has a "Header" and then the payload in a "Payload"
    if outer_type_name == "gw":
        if "Payload" not in content.keys():
            raise GwTypeError(f"Type Gw must include Payload! Keys: <{content.keys()}>")
        content = content["Payload"]
        if "TypeName" not in content.keys():
            raise GwTypeError(f"gw Payload must have TypeName. Keys: {content.keys()}")

    if content["TypeName"] not in TypeMakerByName.keys():
        return None
    codec = TypeMakerByName[content["TypeName"]]
    return codec.dict_to_tuple(content)


def serialize(t: HeartbeatA) -> bytes:
    """
    Given an instance of a pydantic BaseModel class associated to a type,
    returns the approriate instance of the serialized type.

    Raises: GwTypeError if t fails authentication

    """
    return t.as_type()
