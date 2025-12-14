"""Type channel.readings, version 002"""

from typing import List, Literal

from gw.named_types import GwBase
from pydantic import StrictInt, model_validator
from typing_extensions import Self

from gjk.property_format import (
    SpaceheatName,
    UTCMilliseconds,
)


class ChannelReadings(GwBase):
    channel_name: SpaceheatName
    value_list: List[StrictInt]
    scada_read_time_unix_ms_list: List[UTCMilliseconds]
    type_name: Literal["channel.readings"] = "channel.readings"
    version: Literal["002"] = "002"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: ListLengthConsistency.
        ValueList and ScadaReadTimeUnixMsList must have the same length.
        """
        # Implement check for axiom 1"
        return self
