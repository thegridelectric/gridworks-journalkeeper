"""Type gt.sh.booleanactuator.cmd.status, version 101"""

import json
import logging
from typing import Any, Dict, List, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from gjk.type_helpers.property_format import (
    check_is_left_right_dot,
    check_is_reasonable_unix_time_ms,
)

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GtShBooleanactuatorCmdStatus(BaseModel):
    """
    Boolean  Actuator Driver Command Status Package.

    This is a subtype of the status message sent from a SCADA to its AtomicTNode. It contains
    a list of all the commands that a particular boolean actuator actor has reported as sending
    as actuation commands to its driver in the last transmission period (typically 5 minutes).

    [More info](https://gridworks.readthedocs.io/en/latest/relay-state.html)
    """

    sh_node_name: str
    relay_state_command_list: List[int]
    command_time_unix_ms_list: List[int]
    type_name: Literal["gt.sh.booleanactuator.cmd.status"] = (
        "gt.sh.booleanactuator.cmd.status"
    )
    version: Literal["101"] = "101"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        populate_by_name=True,
    )

    @field_validator("sh_node_name")
    @classmethod
    def _check_sh_node_name(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"ShNodeName failed LeftRightDot format validation: {e}"
            ) from e
        return v

    @field_validator("relay_state_command_list")
    @classmethod
    def check_relay_state_command_list(cls, v: List[int]) -> List[int]:
        """
        Axiom : RelayStateCommandLIst must be all 0s and 1s.
        """
        # Implement Axiom(s)
        return v

    @field_validator("command_time_unix_ms_list")
    @classmethod
    def _check_command_time_unix_ms_list(cls, v: List[int]) -> List[int]:
        try:
            for elt in v:
                check_is_reasonable_unix_time_ms(elt)
        except ValueError as e:
            raise ValueError(
                f"CommandTimeUnixMsList element failed ReasonableUnixTimeMs format validation: {e}",
            ) from e
        return v

    @classmethod
    def from_dict(cls, d: dict) -> "GtShBooleanactuatorCmdStatus":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "GtShBooleanactuatorCmdStatus":
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
        return self.plain_enum_dict()

    def plain_enum_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        return d

    def enum_encoded_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the gt.sh.booleanactuator.cmd.status.101 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    def __hash__(self) -> int:
        # Can use as keys in dicts
        return hash(type(self), *tuple(self.__dict__.values()))
