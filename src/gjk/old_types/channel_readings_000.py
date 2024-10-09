"""Type channel.readings, version 000"""

from typing import List, Literal

from gw.errors import GwTypeError
from gw.utils import snake_to_pascal
from pydantic import ConfigDict, StrictInt, model_validator
from typing_extensions import Self

from gjk.property_format import UTCMilliseconds, UUID4Str
from gjk.types.gw_base import GwBase


class ChannelReadings000(GwBase):
    channel_id: UUID4Str
    value_list: List[StrictInt]
    scada_read_time_unix_ms_list: List[UTCMilliseconds]
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
