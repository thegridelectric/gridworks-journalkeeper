import json
from typing import Optional

from gw.errors import GwTypeError

from gjk.types.asl_types import TypeByName
from gjk.types.gw_base import GwBase


def from_type(msg_bytes: bytes) -> Optional[GwBase]:
    """
    Given an instance of the type (i.e., a serialized byte string for sending
    as a message), returns the appropriate instance of the associated pydantic
    BaseModel class. Returns None if the TypeName is not recogized

    Raises: GwTypeError if msg_bytes fails the type authentication

    Returns: Instance of associated Pydantic object, or None if the
    TypeName is not recognized
    """
    try:
        data = json.loads(msg_bytes.decode("utf-8"))
    except Exception:
        print("failed json loads")
        return None
    return from_dict(data)


def from_dict(data: dict) -> Optional[GwBase]:
    if "TypeName" not in data.keys():
        raise GwTypeError(f"No TypeName - so not a type. Keys: <{data.keys()}>")
    outer_type_name = data["TypeName"]

    # Scada messages all come in a 'gw' incomplete type

    # which has a "Header" and then the payload in a "Payload"
    if outer_type_name == "gw":
        if "Payload" not in data.keys():
            raise GwTypeError(f"Type Gw must include Payload! Keys: <{data.keys()}>")
        data = data["Payload"]
        if "TypeName" not in data.keys():
            raise GwTypeError(f"gw Payload must have TypeName. Keys: {data.keys()}")

    if data["TypeName"] not in TypeByName:
        return None

    return TypeByName[data["TypeName"]].from_dict(data)
