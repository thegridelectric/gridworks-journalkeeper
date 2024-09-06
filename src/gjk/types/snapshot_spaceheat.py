"""Type snapshot.spaceheat, version 000"""

import json
import logging
from typing import Any, Dict, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError

from gjk.type_helpers.property_format import (
    LeftRightDotStr,
    UUID4Str,
)
from gjk.types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class SnapshotSpaceheat(BaseModel):
    """
    Snapshot.

    Collection of all the latest measurements (timestamped) captured by the SCADA for all of
    its data channels.
    """

    from_g_node_alias: LeftRightDotStr
    from_g_node_instance_id: UUID4Str
    snapshot: TelemetrySnapshotSpaceheat
    type_name: Literal["snapshot.spaceheat"] = "snapshot.spaceheat"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        populate_by_name=True,
    )

    @classmethod
    def from_dict(cls, d: dict) -> "SnapshotSpaceheat":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "SnapshotSpaceheat":
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
        d["Snapshot"] = self.snapshot.to_dict()
        return d

    def enum_encoded_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["Snapshot"] = self.snapshot.to_dict()
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the snapshot.spaceheat.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    def __hash__(self) -> int:
        # Can use as keys in dicts
        return hash(type(self), *tuple(self.__dict__.values()))
