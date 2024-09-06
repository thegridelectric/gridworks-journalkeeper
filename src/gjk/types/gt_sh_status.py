"""Type gt.sh.status, version 110"""

import json
import logging
from typing import Any, Dict, List, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from gjk.type_helpers.property_format import (
    LeftRightDotStr,
    UUID4Str,
    check_is_reasonable_unix_time_s,
)
from gjk.types.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatus
from gjk.types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from gjk.types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GtShStatus(BaseModel):
    """
    Status message sent by a Spaceheat SCADA every 5 minutes
    """

    from_g_node_alias: LeftRightDotStr
    from_g_node_id: UUID4Str
    about_g_node_alias: LeftRightDotStr
    slot_start_unix_s: int
    reporting_period_s: int
    simple_telemetry_list: List[GtShSimpleTelemetryStatus]
    multipurpose_telemetry_list: List[GtShMultipurposeTelemetryStatus]
    booleanactuator_cmd_list: List[GtShBooleanactuatorCmdStatus]
    status_uid: UUID4Str
    type_name: Literal["gt.sh.status"] = "gt.sh.status"
    version: Literal["110"] = "110"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        populate_by_name=True,
    )

    @field_validator("slot_start_unix_s")
    @classmethod
    def _check_slot_start_unix_s(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_s(v)
        except ValueError as e:
            raise ValueError(
                f"SlotStartUnixS failed ReasonableUnixTimeS format validation: {e}",
            ) from e
        return v

    @classmethod
    def from_dict(cls, d: dict) -> "GtShStatus":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "GtShStatus":
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
        d["SimpleTelemetryList"] = [elt.to_dict() for elt in self.simple_telemetry_list]
        d["MultipurposeTelemetryList"] = [
            elt.to_dict() for elt in self.multipurpose_telemetry_list
        ]
        d["BooleanactuatorCmdList"] = [
            elt.to_dict() for elt in self.booleanactuator_cmd_list
        ]
        return d

    def enum_encoded_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["SimpleTelemetryList"] = [elt.to_dict() for elt in self.simple_telemetry_list]
        d["MultipurposeTelemetryList"] = [
            elt.to_dict() for elt in self.multipurpose_telemetry_list
        ]
        d["BooleanactuatorCmdList"] = [
            elt.to_dict() for elt in self.booleanactuator_cmd_list
        ]
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the gt.sh.status.110 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    def __hash__(self) -> int:
        # Can use as keys in dicts
        return hash(type(self), *tuple(self.__dict__.values()))
