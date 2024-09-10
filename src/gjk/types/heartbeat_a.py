"""Type heartbeat.a, version 001"""

import json
import logging
from typing import Any, Dict, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class HeartbeatA(BaseModel):
    """
    Used to check that an actor can both send and receive messages.

    Payload for direct messages sent back and forth between actors, for example a Supervisor
    and one of its subordinates.

    [More info](https://gridworks.readthedocs.io/en/latest/g-node-instance.html)
    """

    type_name: Literal["heartbeat.a"] = "heartbeat.a"
    version: Literal["001"] = "001"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        frozen=True,
        populate_by_name=True,
    )

    @classmethod
    def from_dict(cls, d: dict) -> "HeartbeatA":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "HeartbeatA":
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing must result in dict!\n <{b}>")
        return cls.from_dict(d)

    def to_dict(self) -> Dict[str, Any]:
        """
        Handles lists of enums differently than model_dump
        """
        d = self.model_dump(exclude_none=True, by_alias=True)
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the heartbeat.a.001 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    def __hash__(self) -> int:
        # Can use as keys in dicts
        return hash(type(self), *tuple(self.__dict__.values()))

    @classmethod
    def type_name_value(cls) -> str:
        return "heartbeat.a"
