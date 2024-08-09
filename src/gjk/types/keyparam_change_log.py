"""Type keyparam.change.log, version 000"""

import json
import logging
import os
from typing import Any, Dict, Literal

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator

from gjk.enums import KindOfParam

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class KeyparamChangeLog(BaseModel):
    """
    Key Param Change Record.

    The keyparam.change.record type is designed for straightforward logging of important parameter
    changes in the SCADA and AtomicTNode code for transactive space-heating systems. Check out
    the details in [gridworks-atn]( https://github.com/thegridelectric/gridworks-atn) and [gw-scada-spaceheat-python](https://github.com/thegridelectric/gw-scada-spaceheat-python).
    It's made for humans—developers and system maintainers—to easily create and reference records
    of significant changes. Keep it short and sweet. We suggest using a "Before" and "After"
    attribute pattern to include the changed value, focusing for example on specific components
    rather than the entire hardware layout.
    """

    about_node_alias: str = Field(
        title="AboutNodeAlias",
        description=(
            "The GNode (for example, the SCADA or the AtomicTNode) whose parameter is getting "
            "changed."
        ),
    )
    change_time_utc: str = Field(
        title="Change Time Utc",
        description=(
            "The time of the change. Err on the side of making sure the original parameter was "
            "used by the code at all times prior to this time. Do not be off by more than 5 minutes."
        ),
    )
    author: str = Field(
        title="Author",
        description="The person making the change.",
    )
    param_name: str = Field(
        title="ParamName",
        description=(
            "This may not be unique or even particularly well-defined on its own. But this can "
            "set the context for the recommended 'Before' and 'After' fields associated to this "
            "type."
        ),
    )
    description: str = Field(
        title="Description",
        description=(
            "Clear concise description of the change. Consider including why it is a key parameter."
        ),
    )
    kind: KindOfParam = Field(
        title="Kind of Param",
        description=(
            "This should provide a developer with the information they need to locate the parameter "
            "and its use within the relevant code base."
        ),
    )
    type_name: Literal["keyparam.change.log"] = "keyparam.change.log"
    version: Literal["000"] = "000"

    class Config:
        extra = "allow"
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

    @field_validator("change_time_utc")
    @classmethod
    def _check_change_time_utc(cls, v: str) -> str:
        try:
            check_is_log_style_date_with_millis(v)
        except ValueError as e:
            raise ValueError(
                f"ChangeTimeUtc failed LogStyleDateWithMillis format validation: {e}",
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
        d["Kind"] = d["Kind"].value
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
        del d["Kind"]
        d["KindGtEnumSymbol"] = KindOfParam.value_to_symbol(self.kind)
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the keyparam.change.log.000 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class KeyparamChangeLogMaker:
    type_name = "keyparam.change.log"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: KeyparamChangeLog) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> KeyparamChangeLog:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a keyparam.change.log.000 type

        Returns:
            KeyparamChangeLog instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> KeyparamChangeLog:
        """
        Translates a dict representation of a keyparam.change.log.000 message object
        into the Python class object.
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "AboutNodeAlias" not in d2.keys():
            raise GwTypeError(f"dict missing AboutNodeAlias: <{d2}>")
        if "ChangeTimeUtc" not in d2.keys():
            raise GwTypeError(f"dict missing ChangeTimeUtc: <{d2}>")
        if "Author" not in d2.keys():
            raise GwTypeError(f"dict missing Author: <{d2}>")
        if "ParamName" not in d2.keys():
            raise GwTypeError(f"dict missing ParamName: <{d2}>")
        if "Description" not in d2.keys():
            raise GwTypeError(f"dict missing Description: <{d2}>")
        if "KindGtEnumSymbol" in d2.keys():
            value = KindOfParam.symbol_to_value(d2["KindGtEnumSymbol"])
            d2["Kind"] = KindOfParam(value)
            del d2["KindGtEnumSymbol"]
        elif "Kind" in d2.keys():
            if d2["Kind"] not in KindOfParam.values():
                d2["Kind"] = KindOfParam.default()
            else:
                d2["Kind"] = KindOfParam(d2["Kind"])
        else:
            raise GwTypeError(
                f"both KindGtEnumSymbol and Kind missing from dict <{d2}>",
            )
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret keyparam.change.log version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return KeyparamChangeLog(**d3)


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


def check_is_log_style_date_with_millis(v: str) -> None:
    """Checks LogStyleDateWithMillis format

    LogStyleDateWithMillis format:  YYYY-MM-DDTHH:mm:ss.SSS

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LogStyleDateWithMillis format.
        In particular the milliseconds must have exactly 3 digits.
    """
    from datetime import datetime

    try:
        datetime.fromisoformat(v)
    except ValueError as e:
        raise ValueError(f"{v} is not in LogStyleDateWithMillis format") from e
    # The python fromisoformat allows for either 3 digits (milli) or 6 (micro)
    # after the final period. Make sure its 3
    milliseconds_part = v.split(".")[1]
    if len(milliseconds_part) != 3:
        raise ValueError(
            f"{v} is not in LogStyleDateWithMillis format."
            " Milliseconds must have exactly 3 digits"
        )
