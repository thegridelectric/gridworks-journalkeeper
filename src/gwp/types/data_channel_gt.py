"""Type data.channel.gt, version 000"""

import json
import logging
from typing import Any
from typing import Dict
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case
from gw.utils import pascal_to_snake
from gw.utils import snake_to_pascal
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from gwp.enums import TelemetryName as EnumTelemetryName


LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class DataChannelGt(BaseModel):
    """
    Data Channel.

    A data channel is a concept of some collection of readings that share all characteristics
    other than time.
    """

    name: str = Field(
        title="Name",
        description=(
            "The Channel Name is meant to be the local unique identifier for the channel within "
            "the context of a specific TerminalAsset. In addition to local uniqueness, it is "
            "immutable. It is designed to be the key that time series data is sorted by in analysis, "
            "as well as a useful way of referencing a channel within Scada code."
        ),
    )
    display_name: str = Field(
        title="Display Name",
        description=(
            "This display name is the handle for the data channel. It is meant to be set by the "
            "person/people who will be analyzing time series data. It is only expected to be "
            "unique within the data channels associated to a specific Terminal Asset. Mutable."
        ),
    )
    about_node_name: str = Field(
        title="About Name",
        description="The name of the SpaceheatNode whose physical quantities are getting captured.",
    )
    captured_by_node_name: str = Field(
        title="Captured By Name",
        description=(
            "The name of the SpaceheatNode that is capturing the physical quantities (which can "
            "be AboutName but does not have to be)."
        ),
    )
    telemetry_name: EnumTelemetryName = Field(
        title="Telemetry Name",
        description="The name of the physical quantity getting measured.",
    )
    id: str = Field(
        title="Id",
        description=(
            "Meant to be an immutable identifier that is globally unique (i.e., across terminal "
            "assets)."
        ),
    )
    type_name: Literal["data.channel.gt"] = "data.channel.gt"
    version: Literal["000"] = "000"

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("name")
    def _check_name(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(f"Name failed SpaceheatName format validation: {e}")
        return v

    @field_validator("about_node_name")
    def _check_about_node_name(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(
                f"AboutNodeName failed SpaceheatName format validation: {e}"
            )
        return v

    @field_validator("captured_by_node_name")
    def _check_captured_by_node_name(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(
                f"CapturedByNodeName failed SpaceheatName format validation: {e}"
            )
        return v

    @field_validator("id")
    def _check_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(f"Id failed UuidCanonicalTextual format validation: {e}")
        return v

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        data.channel.gt.000 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        data.channel.gt.000 type. Unlike the standard python dict method,
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
        del d["TelemetryName"]
        d["TelemetryNameGtEnumSymbol"] = EnumTelemetryName.value_to_symbol(
            self.telemetry_name
        )
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the data.channel.gt.000 representation.

        Instances in the class are python-native representations of data.channel.gt.000
        objects, while the actual data.channel.gt.000 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is DataChannelGt.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class DataChannelGt_Maker:
    type_name = "data.channel.gt"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: DataChannelGt) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> DataChannelGt:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> DataChannelGt:
        """
        Deserialize a dictionary representation of a data.channel.gt.000 message object
        into a DataChannelGt python object for internal use.

        This is the near-inverse of the DataChannelGt.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a GwTypeError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           GwTypeError: if the dict cannot be turned into a DataChannelGt object.

        Returns:
            DataChannelGt
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "Name" not in d2.keys():
            raise GwTypeError(f"dict missing Name: <{d2}>")
        if "DisplayName" not in d2.keys():
            raise GwTypeError(f"dict missing DisplayName: <{d2}>")
        if "AboutNodeName" not in d2.keys():
            raise GwTypeError(f"dict missing AboutNodeName: <{d2}>")
        if "CapturedByNodeName" not in d2.keys():
            raise GwTypeError(f"dict missing CapturedByNodeName: <{d2}>")
        if "TelemetryNameGtEnumSymbol" not in d2.keys():
            raise GwTypeError(f"TelemetryNameGtEnumSymbol missing from dict <{d2}>")
        value = EnumTelemetryName.symbol_to_value(d2["TelemetryNameGtEnumSymbol"])
        d2["TelemetryName"] = EnumTelemetryName(value)
        del d2["TelemetryNameGtEnumSymbol"]
        if "Id" not in d2.keys():
            raise GwTypeError(f"dict missing Id: <{d2}>")
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret data.channel.gt version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return DataChannelGt(**d3)


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


def check_is_uuid_canonical_textual(v: str) -> None:
    """Checks UuidCanonicalTextual format

    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not UuidCanonicalTextual format
    """
    try:
        x = v.split("-")
    except AttributeError as e:
        raise ValueError(f"Failed to split on -: {e}")
    if len(x) != 5:
        raise ValueError(f"<{v}> split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError:
            raise ValueError(f"Words of <{v}> are not all hex")
    if len(x[0]) != 8:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[1]) != 4:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[2]) != 4:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[3]) != 4:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[4]) != 12:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
