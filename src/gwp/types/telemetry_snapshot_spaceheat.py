"""Type telemetry.snapshot.spaceheat, version 000"""

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
from pydantic import model_validator
from typing_extensions import Self

from gwp.enums import TelemetryName


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
    def _check_report_time_unix_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"ReportTimeUnixMs failed ReasonableUnixTimeMs format validation: {e}"
            )
        return v

    @field_validator("about_node_alias_list")
    def _check_about_node_alias_list(cls, v: List[str]) -> List[str]:
        for elt in v:
            try:
                check_is_left_right_dot(elt)
            except ValueError as e:
                raise ValueError(
                    f"AboutNodeAliasList element {elt} failed LeftRightDot format validation: {e}"
                )
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
        Translate the object into a dictionary representation that can be serialized into a
        telemetry.snapshot.spaceheat.000 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        telemetry.snapshot.spaceheat.000 type. Unlike the standard python dict method,
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
        del d["TelemetryNameList"]
        telemetry_name_list = []
        for elt in self.TelemetryNameList:
            telemetry_name_list.append(TelemetryName.value_to_symbol(elt.value))
        d["TelemetryNameList"] = telemetry_name_list
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the telemetry.snapshot.spaceheat.000 representation.

        Instances in the class are python-native representations of telemetry.snapshot.spaceheat.000
        objects, while the actual telemetry.snapshot.spaceheat.000 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is TelemetrySnapshotSpaceheat.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class TelemetrySnapshotSpaceheat_Maker:
    type_name = "telemetry.snapshot.spaceheat"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: TelemetrySnapshotSpaceheat) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> TelemetrySnapshotSpaceheat:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> TelemetrySnapshotSpaceheat:
        """
        Deserialize a dictionary representation of a telemetry.snapshot.spaceheat.000 message object
        into a TelemetrySnapshotSpaceheat python object for internal use.

        This is the near-inverse of the TelemetrySnapshotSpaceheat.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a GwTypeError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           GwTypeError: if the dict cannot be turned into a TelemetrySnapshotSpaceheat object.

        Returns:
            TelemetrySnapshotSpaceheat
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
            value = TelemetryName.symbol_to_value(elt)
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
