"""Type telemetry.snapshot.spaceheat, version 000"""

import json
import logging
import os
from typing import Any, Dict, List, Literal

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from gjk.enums import TelemetryName

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class TelemetrySnapshotSpaceheat(BaseModel):
    """
    Snapshot of Telemetry Data from a SpaceHeat SCADA.

    A snapshot of all current sensed states, sent from a spaceheat SCADA to its AtomicTNode.
    The nth element of each of the three lists refer to the same reading (i.e., what is getting
    read, what the value is, what the TelemetryNames are.)

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/spaceheat-node.html)
    """

    report_time_unix_ms: int = Field(
        title="ReportTimeUnixMs",
        description=(
            "The time, in unix ms, that the SCADA creates this type. It may not be when the SCADA "
            "sends the type to the atn (for example if Internet is down)."
        ),
    )
    about_node_alias_list: List[str] = Field(
        title="AboutNodeAliases",
        description=(
            "The list of Spaceheat nodes in the snapshot."
            "[More info](https://gridworks-protocol.readthedocs.io/en/latest/spaceheat-node.html)"
        ),
    )
    value_list: List[int] = Field(
        title="ValueList",
    )
    telemetry_name_list: List[TelemetryName] = Field(
        title="TelemetryNameList",
        description="[More info](https://gridworks-protocol.readthedocs.io/en/latest/telemetry-name.html)",
    )
    type_name: Literal["telemetry.snapshot.spaceheat"] = "telemetry.snapshot.spaceheat"
    version: Literal["000"] = "000"

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("report_time_unix_ms")
    @classmethod
    def _check_report_time_unix_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"ReportTimeUnixMs failed ReasonableUnixTimeMs format validation: {e}",
            ) from e
        return v

    @field_validator("about_node_alias_list")
    @classmethod
    def _check_about_node_alias_list(cls, v: List[str]) -> List[str]:
        for elt in v:
            try:
                check_is_left_right_dot(elt)
            except ValueError as e:
                raise ValueError(
                    f"AboutNodeAliasList element {elt} failed LeftRightDot format validation: {e}",
                ) from e
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: ListLengthConsistency.
        AboutNodeAliastList, ValueList and TelemetryNameList must all have the same length.
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
        del d["TelemetryNameList"]
        telemetry_name_list = []
        for elt in self.telemetry_name_list:
            telemetry_name_list.append(elt.value)
        d["TelemetryNameList"] = telemetry_name_list
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
        del d["TelemetryNameList"]
        telemetry_name_list = []
        for elt in self.telemetry_name_list:
            telemetry_name_list.append(TelemetryName.value_to_symbol(elt.value))
        d["TelemetryNameList"] = telemetry_name_list
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the telemetry.snapshot.spaceheat.000 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class TelemetrySnapshotSpaceheatMaker:
    type_name = "telemetry.snapshot.spaceheat"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: TelemetrySnapshotSpaceheat) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> TelemetrySnapshotSpaceheat:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a telemetry.snapshot.spaceheat.000 type

        Returns:
            TelemetrySnapshotSpaceheat instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> TelemetrySnapshotSpaceheat:
        """
        Translates a dict representation of a telemetry.snapshot.spaceheat.000 message object
        into the Python class object.
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "ReportTimeUnixMs" not in d2.keys():
            raise GwTypeError(f"dict missing ReportTimeUnixMs: <{d2}>")
        if "AboutNodeAliasList" not in d2.keys():
            raise GwTypeError(f"dict missing AboutNodeAliasList: <{d2}>")
        if "ValueList" not in d2.keys():
            raise GwTypeError(f"dict missing ValueList: <{d2}>")
        if "TelemetryNameList" not in d2.keys():
            raise GwTypeError(f"dict <{d2}> missing TelemetryNameList")
        if not isinstance(d2["TelemetryNameList"], List):
            raise GwTypeError("TelemetryNameList must be a List!")
        telemetry_name_list = []
        for elt in d2["TelemetryNameList"]:
            if elt in TelemetryName.symbols():
                value = TelemetryName.symbol_to_value(elt)
            elif elt in TelemetryName.values():
                value = elt
            else:
                value = TelemetryName.default()
            telemetry_name_list.append(TelemetryName(value))
        d2["TelemetryNameList"] = telemetry_name_list
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret telemetry.snapshot.spaceheat version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return TelemetrySnapshotSpaceheat(**d3)


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
