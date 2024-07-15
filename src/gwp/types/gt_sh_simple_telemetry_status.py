"""Type gt.sh.simple.telemetry.status, version 100"""

import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic.alias_generators import to_pascal
from pydantic.alias_generators import to_snake

from gwp.enums import TelemetryName as EnumTelemetryName


LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GtShSimpleTelemetryStatus(BaseModel):
    """
    Data read from a SimpleSensor run by a SpaceHeat SCADA.

    A list of readings from a simple sensor for a Spaceheat SCADA. Designed as part of a status
    message sent from the SCADA to its AtomicTNode typically once every 5 minutes. The nth element
    of each of its two lists refer to the same reading (i.e. what the value is, when it was
    read).

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/simple-sensor.html)
    """

    sh_node_alias: str = Field(
        title="SpaceheatNodeAlias",
        description="The Alias of the SimpleSensor associated to the readings",
    )
    telemetry_name: EnumTelemetryName = Field(
        title="TelemetryName",
        description=(
            "The TelemetryName of the readings. This is used to interpet the meaning of the reading "
            "values. For example, WaterTempCTimes1000 means the reading is measuring the temperature "
            "of water, in Celsius multiplied by 1000. So a value of 37000 would be a reading "
            "of 37 deg C."
            "[More info](https://gridworks-protocol.readthedocs.io/en/latest/enums.html#gridworks-protocol.enums.TelemetryName)"
        ),
    )
    value_list: List[int] = Field(
        title="List of Values",
        description="The values of the readings.",
    )
    read_time_unix_ms_list: List[int] = Field(
        title="List of Read Times",
        description="The times that the SImpleSensor took the readings, in unix milliseconds",
    )
    type_name: Literal["gt.sh.simple.telemetry.status"] = (
        "gt.sh.simple.telemetry.status"
    )
    version: Literal["100"] = "100"

    class Config:
        populate_by_name = True
        alias_generator = to_pascal

    @field_validator("sh_node_alias")
    def _check_sh_node_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(f"ShNodeAlias failed LeftRightDot format validation: {e}")
        return v

    @field_validator("read_time_unix_ms_list")
    def _check_read_time_unix_ms_list(cls, v: List[int]) -> List[int]:
        for elt in v:
            try:
                check_is_reasonable_unix_time_ms(elt)
            except ValueError as e:
                raise ValueError(
                    f"ReadTimeUnixMsList element {elt} failed ReasonableUnixTimeMs format validation: {e}"
                )
        return v

    @model_validator
    def check_axiom_1(cls, v: dict) -> dict:
        """
        Axiom 1: ListLengthConsistency.
        ValueList and ReadTimeUnixMsList must have the same length.
        """
        # TODO: Implement check for axiom 1"
        return v

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        gt.sh.simple.telemetry.status.100 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        gt.sh.simple.telemetry.status.100 type. Unlike the standard python dict method,
        it makes the following substantive changes:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.
        """
        d = {
            to_pascal(key): value
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
        Serialize to the gt.sh.simple.telemetry.status.100 representation.

        Instances in the class are python-native representations of gt.sh.simple.telemetry.status.100
        objects, while the actual gt.sh.simple.telemetry.status.100 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is GtShSimpleTelemetryStatus.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class GtShSimpleTelemetryStatus_Maker:
    type_name = "gt.sh.simple.telemetry.status"
    version = "100"

    @classmethod
    def tuple_to_type(cls, tuple: GtShSimpleTelemetryStatus) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> GtShSimpleTelemetryStatus:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtShSimpleTelemetryStatus:
        """
        Deserialize a dictionary representation of a gt.sh.simple.telemetry.status.100 message object
        into a GtShSimpleTelemetryStatus python object for internal use.

        This is the near-inverse of the GtShSimpleTelemetryStatus.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a GwTypeError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           GwTypeError: if the dict cannot be turned into a GtShSimpleTelemetryStatus object.

        Returns:
            GtShSimpleTelemetryStatus
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "ShNodeAlias" not in d2.keys():
            raise GwTypeError(f"dict missing ShNodeAlias: <{d2}>")
        if "TelemetryNameGtEnumSymbol" not in d2.keys():
            raise GwTypeError(f"TelemetryNameGtEnumSymbol missing from dict <{d2}>")
        value = EnumTelemetryName.symbol_to_value(d2["TelemetryNameGtEnumSymbol"])
        d2["TelemetryName"] = EnumTelemetryName(value)
        del d2["TelemetryNameGtEnumSymbol"]
        if "ValueList" not in d2.keys():
            raise GwTypeError(f"dict missing ValueList: <{d2}>")
        if "ReadTimeUnixMsList" not in d2.keys():
            raise GwTypeError(f"dict missing ReadTimeUnixMsList: <{d2}>")
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "100":
            LOGGER.debug(
                f"Attempting to interpret gt.sh.simple.telemetry.status version {d2['Version']} as version 100"
            )
            d2["Version"] = "100"
        d3 = {to_snake(key): value for key, value in d2.items()}
        return GtShSimpleTelemetryStatus(**d3)


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods, with
    the most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
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
        if not word.isalnum():
            raise ValueError(f"words of <{v}> split by by '.' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of <{v}> must be lowercase.")


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
