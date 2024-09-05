"""Type gridworks.event.snapshot.spaceheat, version 000"""

import copy
import json
import logging
import os
from typing import Any, Dict, Literal

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator

from gjk.enums import TelemetryName
from gjk.types.snapshot_spaceheat import SnapshotSpaceheat, SnapshotSpaceheatMaker

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GridworksEventSnapshotSpaceheat(BaseModel):
    """
    This is a gjk wrapper around a gt.sh.status message that includes the src (which should
    always be the GNodeAlias for the Scada actor), a unique message id (which is immutable once
    the gt.sh.status message is created, and does not change if the SCADA re-sends the message
    due to no ack from AtomicTNode) and a timestamp for when the message was created.
    """

    message_id: str = Field(
        title="MessageId",
        description=(
            "This is a unique immutable id assigned to the snapshot payload when created by the "
            "SCADA. If the original message is not acked by the AtomicTNode, the entire gridworks.event "
            "is stored locally and re-sent later when AtomicTNode comms are re-established. (with "
            "this same MessageId)"
        ),
    )
    time_n_s: int = Field(
        title="TimeNS",
        description="The time in epoch nanoseconds that the SCADA created the snapshot.",
    )
    src: str = Field(
        title="Src",
        description="The GNodeAlias of the SCADA sending the snapshot.",
    )
    snap: SnapshotSpaceheat = Field(
        title="Snap",
    )
    type_name: Literal["gridworks.event.snapshot.spaceheat"] = (
        "gridworks.event.snapshot.spaceheat"
    )
    version: Literal["000"] = "000"

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("message_id")
    @classmethod
    def _check_message_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"MessageId failed UuidCanonicalTextual format validation: {e}",
            ) from e
        return v

    @field_validator("src")
    @classmethod
    def _check_src(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(f"Src failed LeftRightDot format validation: {e}") from e
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
        d["Snap"] = self.snap.as_dict()
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
        d["Snap"] = self.snap.as_dict()
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the gridworks.event.snapshot.spaceheat.000 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class GridworksEventSnapshotSpaceheatMaker:
    type_name = "gridworks.event.snapshot.spaceheat"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: GridworksEventSnapshotSpaceheat) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> GridworksEventSnapshotSpaceheat:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a gridworks.event.snapshot.spaceheat.000 type

        Returns:
            GridworksEventSnapshotSpaceheat instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> GridworksEventSnapshotSpaceheat:
        """
        Translates a dict representation of a gridworks.event.snapshot.spaceheat.000 message object
        into the Python class object.
        """
        e = cls.first_season_fix(d)
        for key in e.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(e)
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "MessageId" not in d2.keys():
            raise GwTypeError(f"dict missing MessageId: <{d2}>")
        if "TimeNS" not in d2.keys():
            raise GwTypeError(f"dict missing TimeNS: <{d2}>")
        if "Src" not in d2.keys():
            raise GwTypeError(f"dict missing Src: <{d2}>")
        if "Snap" not in d2.keys():
            raise GwTypeError(f"dict missing Snap: <{d2}>")
        if not isinstance(d2["Snap"], dict):
            raise GwTypeError(f"Snap <{d2['Snap']}> must be a SnapshotSpaceheat!")
        snap = SnapshotSpaceheatMaker.dict_to_tuple(d2["Snap"])
        d2["Snap"] = snap
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret gridworks.event.snapshot.spaceheat version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return GridworksEventSnapshotSpaceheat(**d3)

    @classmethod
    def first_season_fix(cls, d: dict[str, Any]) -> dict[str, Any]:
        """
        Makes key "snap" -> "Snap", following the rule that
        all GridWorks types must have PascalCase keys
        """

        d2 = copy.deepcopy(d)

        if "snap" in d2.keys():
            d2["Snap"] = d2["snap"]
            del d2["snap"]

        if "Snap" not in d2.keys():
            raise GwTypeError(f"dict missing Snap: <{d2.keys()}>")

        if "Snapshot" not in d2["Snap"].keys():
            raise GwTypeError(f"dict['Snap'] missing Snapshot: <{d2['Snap'].keys()}>")

        snapshot = d2["Snap"]["Snapshot"]
        # replace values with symbols for TelemetryName in SimpleTelemetryList
        if "TelemetryNameList" not in snapshot.keys():
            raise Exception(
                f"Snapshot does not have TelemetryNameList in keys! simple.key()): <{snapshot.keys()}>"
            )
        telemetry_name_list = snapshot["TelemetryNameList"]
        new_list = []
        for tn in telemetry_name_list:
            new_list.append(TelemetryName.value_to_symbol(tn))
        snapshot["TelemetryNameList"] = new_list

        d2["Snap"]["Snapshot"] = snapshot
        d2["Version"] = "000"
        return d2


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
        raise ValueError(f"Failed to split on -: {e}") from e
    if len(x) != 5:
        raise ValueError(f"<{v}> split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError as e:
            raise ValueError(f"Words of <{v}> are not all hex") from e
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
