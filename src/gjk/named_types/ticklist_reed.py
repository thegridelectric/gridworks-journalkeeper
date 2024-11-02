"""Type ticklist.reed, version 101"""

from typing import List, Literal, Optional

from gw.named_types import GwBase
from pydantic import model_validator
from typing_extensions import Self


class TicklistReed(GwBase):
    hw_uid: str
    first_tick_timestamp_nano_second: Optional[int]
    relative_millisecond_list: List[int]
    pico_before_post_timestamp_nano_second: int
    type_name: Literal["ticklist.reed"] = "ticklist.reed"
    version: Literal["101"] = "101"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        if (
            self.first_tick_timestamp_nano_second is None
            and len(self.relative_millisecond_list) > 0
        ):
            raise ValueError(
                "FirstTickTimestampNanoSecond is None but RelativeMillisecondList has nonzero length!"
            )
        if (
            self.first_tick_timestamp_nano_second
            and len(self.relative_millisecond_list) == 0
        ):
            raise ValueError(
                "FirstTickTimestampNanoSecond exists but RelativeMillisecondList has no elements!"
            )
        return self
