"""Type gt.sh.booleanactuator.cmd.status, version 101"""

import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case
from gw.utils import pascal_to_snake
from gw.utils import snake_to_pascal
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


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
    def _check_sh_node_name(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(f"ShNodeName failed LeftRightDot format validation: {e}")
        return v

    @field_validator("relay_state_command_list")
    def check_relay_state_command_list(cls, v: List[int]) -> List[int]:
        """
        Axiom : RelayStateCommandLIst must be all 0s and 1s.
        """
        ...
        # TODO: Implement Axiom(s)

    @field_validator("command_time_unix_ms_list")
    def _check_command_time_unix_ms_list(cls, v: List[int]) -> List[int]:
        for elt in v:
            try:
                check_is_reasonable_unix_time_ms(elt)
            except ValueError as e:
                raise ValueError(
                    f"CommandTimeUnixMsList element {elt} failed ReasonableUnixTimeMs format validation: {e}"
                )
        return v

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        gt.sh.booleanactuator.cmd.status.101 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        gt.sh.booleanactuator.cmd.status.101 type. Unlike the standard python dict method,
        it makes the following substantive changes:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.
        """
        d = {
            snake_to_pascal(key): value
            for key, value in self.model_dump().items()
            if value is not None
        }
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the gt.sh.booleanactuator.cmd.status.101 representation.

        Instances in the class are python-native representations of gt.sh.booleanactuator.cmd.status.101
        objects, while the actual gt.sh.booleanactuator.cmd.status.101 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is GtShBooleanactuatorCmdStatus.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class GtShBooleanactuatorCmdStatus_Maker:
    type_name = "gt.sh.booleanactuator.cmd.status"
    version = "101"

    @classmethod
    def tuple_to_type(cls, tuple: GtShBooleanactuatorCmdStatus) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> GtShBooleanactuatorCmdStatus:
        """
        Given a serialized JSON type object, returns the Python class object.
        """
        try:
            d = json.loads(t)
        except TypeError:
            raise GwTypeError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing <{t}> must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtShBooleanactuatorCmdStatus:
        """
        Deserialize a dictionary representation of a gt.sh.booleanactuator.cmd.status.101 message object
        into a GtShBooleanactuatorCmdStatus python object for internal use.

        This is the near-inverse of the GtShBooleanactuatorCmdStatus.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a GwTypeError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           GwTypeError: if the dict cannot be turned into a GtShBooleanactuatorCmdStatus object.

        Returns:
            GtShBooleanactuatorCmdStatus
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
    from datetime import datetime
    from datetime import timezone

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
    Lowercase words separated by periods, where word characters can be alphanumeric
    or a hyphen, and the first word starts with an alphabet character.

    Args:
        candidate (str): The string to be validated.

    Raises:
        ValueError: If the provided string is not in SpaceheatName format.
    """
    from typing import List

    try:
        x: List[str] = v.split(".")
    except:
        raise ValueError(f"Failed to seperate <{v}> into words with split'.'")
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