"""Type channel.readings, version 000"""

from typing import List, Literal, Self

from gw.named_types import GwBase
from pydantic import StrictInt, model_validator

from gjk.property_format import SpaceheatName, UTCMilliseconds, UUID4Str


class ChannelReadings001(GwBase):
    channel_name: SpaceheatName
    channel_id: UUID4Str
    value_list: list[StrictInt]
    scada_read_time_unix_ms_list: list[UTCMilliseconds]
    type_name: Literal["channel.readings"] = "channel.readings"
    version: Literal["001"] = "001"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: ListLengthConsistency.
        ValueList and ScadaReadTimeUnixMsList must have the same length.
        """
        # Implement check for axiom 1"
        return self
