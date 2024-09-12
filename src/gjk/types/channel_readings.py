"""Type channel.readings, version 000"""

import json
import logging
from typing import Any, Dict, List, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    model_validator,
)
from typing_extensions import Self

from gjk.type_helpers.property_format import (
    ReallyAnInt,
    ReasonableUnixMs,
    UUID4Str,
)

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class ChannelReadings(BaseModel):
    """
    A list of timestamped readings (values) for a data channel. This is meant to be reported
    for non-local consumption (AtomicTNode, other) by a SCADA. Therefore, the data channel is
    referenced by its globally unique identifier. The receiver needs to reference this idea
    against a list of the data channels used by the SCADA for accurate parsing. Replaces both
    GtShSimpleTelemetryStatus and GtShMultipurposeTelemetryStatus
    """

    channel_id: UUID4Str
    value_list: List[ReallyAnInt]
    scada_read_time_unix_ms_list: List[ReasonableUnixMs]
    type_name: Literal["channel.readings"] = "channel.readings"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        frozen=True,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: ListLengthConsistency.
        ValueList and ScadaReadTimeUnixMsList must have the same length.
        """
        if len(self.value_list) != len(self.scada_read_time_unix_ms_list):
            raise GwTypeError(
                "Axiom 1: lists of values and timestamps must be the same length!"
            )
        return self

    @classmethod
    def from_dict(cls, d: dict) -> "ChannelReadings":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "ChannelReadings":
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
        d = self.model_dump(exclude_none=True, by_alias=True)
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the channel.readings.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    @classmethod
    def type_name_value(cls) -> str:
        return "channel.readings"
