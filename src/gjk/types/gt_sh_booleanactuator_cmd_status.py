"""Type gt.sh.booleanactuator.cmd.status, version 101"""

import json
import logging
import os
from typing import Any, Dict, List, Literal

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

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

    sh_node_name: str = Field(
        title="SpaceheatNodeAlias",
        description=(
            "The alias of the spaceheat node that is getting actuated. For example, `a.elt1.relay` "
            "would likely indicate the relay for a resistive element."
            "[More info](https://gridworks-protocol.readthedocs.io/en/latest/boolean-actuator.html)"
        ),
    )
    relay_state_command_list: List[int] = Field(
        title="List of RelayStateCommands",
        description=(
            "This is only intended for use for relays where the two states are either closing "
            "a circuit so that power is on ( '1') or opening it ('0')."
        ),
    )
    command_time_unix_ms_list: List[int] = Field(
        title="List of Command Times",
    )
    type_name: Literal["gt.sh.booleanactuator.cmd.status"] = (
        "gt.sh.booleanactuator.cmd.status"
    )
    version: Literal["101"] = "101"

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

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
        ...
        # TODO: Implement Axiom(s)

    @field_validator("command_time_unix_ms_list")
    @classmethod
    def _check_command_time_unix_ms_list(cls, v: List[int]) -> List[int]:
        for elt in v:
            try:
                check_is_reasonable_unix_time_ms(elt)
            except ValueError as e:
                raise ValueError(
                    f"CommandTimeUnixMsList element {elt} failed ReasonableUnixTimeMs format validation: {e}",
                ) from e
        return v

    def as_dict(self) -> Dict[str, Any]:
        """
        Main step in serializing the object. Encodes enums as their 8-digit random hex symbol if
        settings.encode_enums = 1.
        """
        if ENCODE_ENUMS:
            return self.enum_encoded_dict()
        else:
            return self.plain_enum_dict()

    def plain_enum_dict(self) -> Dict[str, Any]:
        """
        Returns enums as their values.
        """
        d = {
            snake_to_pascal(key): value
            for key, value in self.model_dump().items()
            if value is not None
        }
        return d

    def enum_encoded_dict(self) -> Dict[str, Any]:
        """
        Encodes enums as their 8-digit random hex symbol
        """
        d = {
            snake_to_pascal(key): value
            for key, value in self.model_dump().items()
            if value is not None
        }
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the gt.sh.booleanactuator.cmd.status.101 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class GtShBooleanactuatorCmdStatusMaker:
    type_name = "gt.sh.booleanactuator.cmd.status"
    version = "101"

    @classmethod
    def tuple_to_type(cls, tuple: GtShBooleanactuatorCmdStatus) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> GtShBooleanactuatorCmdStatus:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a gt.sh.booleanactuator.cmd.status.101 type

        Returns:
            GtShBooleanactuatorCmdStatus instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtShBooleanactuatorCmdStatus:
        """
        Translates a dict representation of a gt.sh.booleanactuator.cmd.status.101 message object
        into the Python class object.
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "ShNodeName" not in d2.keys():
            raise GwTypeError(f"dict missing ShNodeName: <{d2}>")
        if "RelayStateCommandList" not in d2.keys():
            raise GwTypeError(f"dict missing RelayStateCommandList: <{d2}>")
        if "CommandTimeUnixMsList" not in d2.keys():
            raise GwTypeError(f"dict missing CommandTimeUnixMsList: <{d2}>")
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "101":
            LOGGER.debug(
                f"Attempting to interpret gt.sh.booleanactuator.cmd.status version {d2['Version']} as version 101"
            )
            d2["Version"] = "101"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return GtShBooleanactuatorCmdStatus(**d3)


def check_is_reasonable_unix_time_ms(v: int) -> None:
    """Checks ReasonableUnixTimeMs format

    ReasonableUnixTimeMs format: unix milliseconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeMs format
    """
    from datetime import datetime, timezone

    start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(3000, 1, 1, tzinfo=timezone.utc)

    start_timestamp_ms = int(start_date.timestamp() * 1000)
    end_timestamp_ms = int(end_date.timestamp() * 1000)

    if v < start_timestamp_ms:
        raise ValueError(f"{v} must be after Jan 1 2000")
    if v > end_timestamp_ms:
        raise ValueError(f"{v} must be before Jan 1 3000")


def check_is_spaceheat_name(v: str) -> None:
    """Check SpaceheatName Format.

    Validates if the provided string adheres to the SpaceheatName format:
    Lowercase alphanumeric words separated by hypens

    Args:
        candidate (str): The string to be validated.

    Raises:
        ValueError: If the provided string is not in SpaceheatName format.
    """
    try:
        x = v.split(".")
    except Exception as e:
        raise ValueError(f"Failed to seperate <{v}> into words with split'.'") from e
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of <{v}> must start with alphabet char."
        )
    for word in x:
        for char in word:
            if not (char.isalnum() or char == "-"):
                raise ValueError(
                    f"words of <{v}> split by by '.' must be alphanumeric or hyphen."
                )
    if not v.islower():
        raise ValueError(f"<{v}> must be lowercase.")
