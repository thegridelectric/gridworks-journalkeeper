"""Type fsm.full.report, version 000"""

import json
import logging
import os
from typing import Any, Dict, List, Literal

import dotenv
from gw.errors import GwTypeError
from gw.utils import is_pascal_case, pascal_to_snake, snake_to_pascal
from pydantic import BaseModel, Field, field_validator

from gjk.types.fsm_atomic_report import FsmAtomicReport, FsmAtomicReportMaker

dotenv.load_dotenv()

ENCODE_ENUMS = int(os.getenv("ENUM_ENCODE", "1"))

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class FsmFullReport(BaseModel):
    """
    There will be cascading events, actions and transitions that will naturally follow a single
    high-level event. This message is designed to encapsulate all of those.

    [More info](https://gridworks-protocol.readthedocs.io/en/latest/finite-state-machines.html)
    """

    from_name: str = Field(
        title="From Name",
        description=(
            "The name (not the handle, so immutable) of the Node issuing the report. This will "
            "typically be the scada node itself."
        ),
    )
    trigger_id: str = Field(
        title="TriggerId",
        description=(
            "Reference uuid for the triggering event that started the cascade of side-effect "
            "actions, events and transitions captured in this report"
        ),
    )
    atomic_list: List[FsmAtomicReport] = Field(
        title="Atomic List",
        description=(
            "The list of cascading events, transitions and actions triggered by a single high-level "
            "event in a hierarchical finite state machine."
        ),
    )
    type_name: Literal["fsm.full.report"] = "fsm.full.report"
    version: Literal["000"] = "000"

    class Config:
        extra = "allow"
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("from_name")
    @classmethod
    def _check_from_name(cls, v: str) -> str:
        try:
            check_is_spaceheat_name(v)
        except ValueError as e:
            raise ValueError(
                f"FromName failed SpaceheatName format validation: {e}"
            ) from e
        return v

    @field_validator("trigger_id")
    @classmethod
    def _check_trigger_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"TriggerId failed UuidCanonicalTextual format validation: {e}",
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
        # Recursively calling as_dict()
        atomic_list = []
        for elt in self.atomic_list:
            atomic_list.append(elt.as_dict())
        d["AtomicList"] = atomic_list
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
        # Recursively calling as_dict()
        atomic_list = []
        for elt in self.atomic_list:
            atomic_list.append(elt.as_dict())
        d["AtomicList"] = atomic_list
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the fsm.full.report.000 representation designed to send in a message.

        Recursively encodes enums as hard-to-remember 8-digit random hex symbols
        unless settings.encode_enums is set to 0.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class FsmFullReportMaker:
    type_name = "fsm.full.report"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: FsmFullReport) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, b: bytes) -> FsmFullReport:
        """
        Given the bytes in a message, returns the corresponding class object.

        Args:
            b (bytes): candidate type instance

        Raises:
           GwTypeError: if the bytes are not a fsm.full.report.000 type

        Returns:
            FsmFullReport instance
        """
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing  must result in dict!\n <{b}>")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> FsmFullReport:
        """
        Translates a dict representation of a fsm.full.report.000 message object
        into the Python class object.
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "FromName" not in d2.keys():
            raise GwTypeError(f"dict missing FromName: <{d2}>")
        if "TriggerId" not in d2.keys():
            raise GwTypeError(f"dict missing TriggerId: <{d2}>")
        if "AtomicList" not in d2.keys():
            raise GwTypeError(f"dict missing AtomicList: <{d2}>")
        if not isinstance(d2["AtomicList"], List):
            raise GwTypeError(f"AtomicList <{d2['AtomicList']}> must be a List!")
        atomic_list = []
        for elt in d2["AtomicList"]:
            if not isinstance(elt, dict):
                raise GwTypeError(
                    f"AtomicList <{d2['AtomicList']}> must be a List of FsmAtomicReport types"
                )
            t = FsmAtomicReportMaker.dict_to_tuple(elt)
            atomic_list.append(t)
        d2["AtomicList"] = atomic_list
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret fsm.full.report version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {pascal_to_snake(key): value for key, value in d2.items()}
        return FsmFullReport(**d3)


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
