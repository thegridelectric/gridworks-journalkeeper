"""Type data.channel.gt, version 001"""

import json
import logging
import os
from typing import Any, Dict, Literal, Optional

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from gjk.enums import TelemetryName
from gjk.models import DataChannelSql

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

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
    telemetry_name: TelemetryName = Field(
        title="Telemetry Name",
        description="The name of the physical quantity getting measured.",
    )
    terminal_asset_alias: str = Field(
        title="Terminal Asset",
        description=(
            "The Terminal Asset GNode for which this data channel is reporting data. For example, "
            "the GNode with alias hw1.isone.me.versant.keene.beech.ta represents the heat pump "
            "thermal storage system in the first GridWorks Millinocket deployment."
        ),
    )
    in_power_metering: Optional[bool] = Field(
        title="In Power Metering",
        description=(
            "This channel is in the sum of the aggregate transactive power metering for the terminal "
            "asset"
        ),
        default=None,
    )
    start_s: Optional[int] = Field(
        title="Start Seconds Epoch Time",
        description=(
            "The epoch time of the first data record associated to a channel. If this value is "
            "None it means no known data yet."
        ),
        default=None,
    )
    id: str = Field(
        title="Id",
        description=(
            "Meant to be an immutable identifier that is globally unique (i.e., across terminal "
            "assets)."
        ),
    )
    type_name: Literal["data.channel.gt"] = "data.channel.gt"
    version: Literal["001"] = "001"

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(f"Name failed SpaceheatName format validation: {e}") from e
        return v

    @field_validator("about_node_name")
    @classmethod
    def _check_about_node_name(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(
                f"AboutNodeName failed SpaceheatName format validation: {e}",
            ) from e
        return v

    @field_validator("captured_by_node_name")
    @classmethod
    def _check_captured_by_node_name(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(
                f"CapturedByNodeName failed SpaceheatName format validation: {e}",
            ) from e
        return v

    @field_validator("terminal_asset_alias")
    @classmethod
    def _check_terminal_asset_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"TerminalAssetAlias failed LeftRightDot format validation: {e}",
            ) from e
        return v

    @field_validator("start_s")
    @classmethod
    def _check_start_s(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        try:
            check_is_reasonable_unix_time_s(v)
        except ValueError as e:
            raise ValueError(
                f"StartS failed ReasonableUnixTimeS format validation: {e}",
            ) from e
        return v

    @field_validator("id")
    @classmethod
    def _check_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"Id failed UuidCanonicalTextual format validation: {e}"
            ) from e
        return v

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Power Metering.
        If InPowerMetering is true then the TelemetryName must be PowerW
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
        d["TelemetryNameGtEnumSymbol"] = TelemetryName.value_to_symbol(
            self.telemetry_name
        )
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the data.channel.gt.001 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def as_sql(self) -> DataChannelSql:
        return DataChannelSql(**self.model_dump())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class DataChannelGtMaker:
    type_name = "data.channel.gt"
    version = "001"

    @classmethod
    def tuple_to_type(cls, tuple: DataChannelGt) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> DataChannelGt:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a data.channel.gt.001 type

        Returns:
            DataChannelGt instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> DataChannelGt:
        """
        Translates a dict representation of a data.channel.gt.001 message object
        into the Python class object.
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
        if "TelemetryNameGtEnumSymbol" in d2.keys():
            value = TelemetryName.symbol_to_value(d2["TelemetryNameGtEnumSymbol"])
            d2["TelemetryName"] = TelemetryName(value)
            del d2["TelemetryNameGtEnumSymbol"]
        elif "TelemetryName" in d2.keys():
            if d2["TelemetryName"] not in TelemetryName.values():
                d2["TelemetryName"] = TelemetryName.default()
            else:
                d2["TelemetryName"] = TelemetryName(d2["TelemetryName"])
        else:
            raise GwTypeError(
                f"both TelemetryNameGtEnumSymbol and TelemetryName missing from dict <{d2}>",
            )
        if "TerminalAssetAlias" not in d2.keys():
            raise GwTypeError(f"dict missing TerminalAssetAlias: <{d2}>")
        if "Id" not in d2.keys():
            raise GwTypeError(f"dict missing Id: <{d2}>")
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "001":
            LOGGER.debug(
                f"Attempting to interpret data.channel.gt version {d2['Version']} as version 001"
            )
            d2["Version"] = "001"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return DataChannelGt(**d3)

    @classmethod
    def orm_to_tuple(cls, orm: DataChannelSql) -> DataChannelGt:
        """
        Given a DataChannelSql object, returns a DataChannelGt object
        """
        data = {
            key: value for key, value in orm.__dict__.items() if not key.startswith("_")
        }
        return DataChannelGt(**data)


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


def check_is_reasonable_unix_time_s(v: int) -> None:
    """Checks ReasonableUnixTimeS format

    ReasonableUnixTimeS format: unix seconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeS format
    """
    from datetime import datetime, timezone

    start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(3000, 1, 1, tzinfo=timezone.utc)

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    if v < start_timestamp:
        raise ValueError(f"{v} must be after Jan 1 2000")
    if v > end_timestamp:
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


def check_is_uuid_canonical_textual(v: str) -> None:
    """Checks UuidCanonicalTextual format

    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not UuidCanonicalTextual format
    """
    phi_fun_check_it_out = 5
    two_cubed_too_cute = 8
    bachets_fun_four = 4
    the_sublime_twelve = 12
    try:
        x = v.split("-")
    except AttributeError as e:
        raise ValueError(f"Failed to split on -: {e}") from e
    if len(x) != phi_fun_check_it_out:
        raise ValueError(f"<{v}> split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError as e:
            raise ValueError(f"Words of <{v}> are not all hex") from e
    if len(x[0]) != two_cubed_too_cute:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[1]) != bachets_fun_four:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[2]) != bachets_fun_four:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[3]) != bachets_fun_four:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
    if len(x[4]) != the_sublime_twelve:
        raise ValueError(f"<{v}> word lengths not 8-4-4-4-12")
