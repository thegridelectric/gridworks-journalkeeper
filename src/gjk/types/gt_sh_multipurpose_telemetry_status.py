"""Type gt.sh.multipurpose.telemetry.status, version 100"""

import json
import logging
import os
from typing import Any, Dict, List, Literal

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from gjk.enums import TelemetryName as EnumTelemetryName

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GtShMultipurposeTelemetryStatus(BaseModel):
    """
    Data read from a MultipurposeSensor run by a Spaceheat SCADA.

    A list of readings about a specific SpaceheatNode made by a MultipurposeSensor node, for
    a Spaceheat SCADA. Designed as part of a status message sent from the SCADA to its AtomicTNode
    typically once every 5 minutes. The nth element of each of its two lists refer to the same
    reading (i.e. what the value is, when it was read).

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/multipurpose-sensor.html)
    """

    about_node_alias: str = Field(
        title="AboutNodeAlias",
        description=(
            "The SpaceheatNode representing the physical object that the sensor reading is collecting "
            "data about. For example, a multipurpose temp sensor that reads 12 temperatures would "
            "have data for 12 different AboutNodeAliases, including say `a.tank1.temp1` for a "
            "temp sensor at the top of a water tank."
            "[More info](https://gridworks-protocol.readthedocs.io/en/latest/spaceheat-node.html)"
        ),
    )
    sensor_node_alias: str = Field(
        title="SensorNodeAlias",
        description="The alias of the SpaceheatNode representing the telemetry device",
    )
    telemetry_name: EnumTelemetryName = Field(
        title="TelemetryName",
        description=(
            "The TelemetryName of the readings. This is used to interpet the meaning of the reading "
            "values. For example, WaterTempCTimes1000 means the reading is measuring the a reading "
            "of 37 deg C."
            "[More info](https://gridworks-protocol.readthedocs.io/en/latest/telemetry-name.html)"
        ),
    )
    value_list: List[int] = Field(
        title="List of Values",
        description="The values of the readings.",
    )
    read_time_unix_ms_list: List[int] = Field(
        title="List of Read Times",
        description="The times that the MultipurposeSensor took the readings, in unix milliseconds",
    )
    type_name: Literal["gt.sh.multipurpose.telemetry.status"] = (
        "gt.sh.multipurpose.telemetry.status"
    )
    version: Literal["100"] = "100"

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("about_node_alias")
    @classmethod
    def _check_about_node_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"AboutNodeAlias failed LeftRightDot format validation: {e}",
            ) from e
        return v

    @field_validator("read_time_unix_ms_list")
    @classmethod
    def _check_read_time_unix_ms_list(cls, v: List[int]) -> List[int]:
        for elt in v:
            try:
                check_is_reasonable_unix_time_ms(elt)
            except ValueError as e:
                raise ValueError(
                    f"ReadTimeUnixMsList element {elt} failed ReasonableUnixTimeMs format validation: {e}",
                ) from e
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: ListLengthConsistency.
        ValueList and ReadTimeUnixMsList must have the same length.
        """
        # TODO: Implement check for axiom 1"
        return self

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
        d["TelemetryName"] = d["TelemetryName"].value
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
        del d["TelemetryName"]
        d["TelemetryNameGtEnumSymbol"] = EnumTelemetryName.value_to_symbol(
            self.telemetry_name
        )
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the gt.sh.multipurpose.telemetry.status.100 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class GtShMultipurposeTelemetryStatusMaker:
    type_name = "gt.sh.multipurpose.telemetry.status"
    version = "100"

    @classmethod
    def tuple_to_type(cls, tuple: GtShMultipurposeTelemetryStatus) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> GtShMultipurposeTelemetryStatus:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a gt.sh.multipurpose.telemetry.status.100 type

        Returns:
            GtShMultipurposeTelemetryStatus instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtShMultipurposeTelemetryStatus:
        """
        Translates a dict representation of a gt.sh.multipurpose.telemetry.status.100 message object
        into the Python class object.
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "AboutNodeAlias" not in d2.keys():
            raise GwTypeError(f"dict missing AboutNodeAlias: <{d2}>")
        if "SensorNodeAlias" not in d2.keys():
            raise GwTypeError(f"dict missing SensorNodeAlias: <{d2}>")
        if "TelemetryNameGtEnumSymbol" in d2.keys():
            value = EnumTelemetryName.symbol_to_value(d2["TelemetryNameGtEnumSymbol"])
            d2["TelemetryName"] = EnumTelemetryName(value)
            del d2["TelemetryNameGtEnumSymbol"]
        elif "TelemetryName" in d2.keys():
            if d2["TelemetryName"] not in EnumTelemetryName.values():
                d2["TelemetryName"] = EnumTelemetryName.default()
            else:
                d2["TelemetryName"] = EnumTelemetryName(d2["TelemetryName"])
        else:
            raise GwTypeError(
                f"both TelemetryNameGtEnumSymbol and TelemetryName missing from dict <{d2}>",
            )
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
                f"Attempting to interpret gt.sh.multipurpose.telemetry.status version {d2['Version']} as version 100"
            )
            d2["Version"] = "100"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return GtShMultipurposeTelemetryStatus(**d3)


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods, with
    the most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
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
    from datetime import datetime, timezone

    start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(3000, 1, 1, tzinfo=timezone.utc)

    start_timestamp_ms = int(start_date.timestamp() * 1000)
    end_timestamp_ms = int(end_date.timestamp() * 1000)

    if v < start_timestamp_ms:
        raise ValueError(f"{v} must be after Jan 1 2000")
    if v > end_timestamp_ms:
        raise ValueError(f"{v} must be before Jan 1 3000")
