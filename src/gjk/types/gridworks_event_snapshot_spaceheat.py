"""Type gridworks.event.snapshot.spaceheat, version 000"""

import json
import logging
from typing import Any, Dict, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from gjk.type_helpers.property_format import (
    UUID4Str,
    check_is_left_right_dot,
)
from gjk.types.snapshot_spaceheat import SnapshotSpaceheat

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

    message_id: UUID4Str
    time_n_s: int
    src: str
    snap: SnapshotSpaceheat
    type_name: Literal["gridworks.event.snapshot.spaceheat"] = (
        "gridworks.event.snapshot.spaceheat"
    )
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        populate_by_name=True,
    )

    @field_validator("src")
    @classmethod
    def _check_src(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(f"Src failed LeftRightDot format validation: {e}") from e
        return v

    @classmethod
    def from_dict(cls, d: dict) -> "GridworksEventSnapshotSpaceheat":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "GridworksEventSnapshotSpaceheat":
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing must result in dict!\n <{b}>")
        return cls.from_dict(d)

    def to_dict(self) -> Dict[str, Any]:
        """
        Handles lists of enums differently than model_dump
        """
        return self.plain_enum_dict()

    def plain_enum_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["Snap"] = self.snap.to_dict()
        return d

    def enum_encoded_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["Snap"] = self.snap.to_dict()
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the gridworks.event.snapshot.spaceheat.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    def __hash__(self) -> int:
        # Can use as keys in dicts
        return hash(type(self), *tuple(self.__dict__.values()))
