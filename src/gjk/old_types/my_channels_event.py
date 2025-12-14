"""Type my.channels.event, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import model_validator
from typing_extensions import Self

from gjk.old_types.my_channels import MyChannels
from gjk.property_format import (
    UTCMilliseconds,
    UUID4Str,
)


class MyChannelsEvent(GwBase):
    message_id: UUID4Str
    time_created_ms: UTCMilliseconds
    src: str
    my_channels: MyChannels
    type_name: Literal["my.channels.event"] = "my.channels.event"
    version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Src is MyChannels.FromGNodeAlias,  MessageId is MyChannels.MessageId, TimeCreatedMs is MyChannels.MessageCreatedMs .
        """
        if self.src != self.my_channels.from_g_node_alias:
            raise ValueError(
                f"Axiom 1 violated! src {self.src} must be MyChannels.FromGNodeAlias {self.my_channels.from_g_node_alias}"
            )
        if self.message_id != self.my_channels.message_id:
            raise ValueError("Axiom 1 violated! MessageId must match")
        if self.time_created_ms != self.my_channels.message_created_ms:
            raise ValueError(
                "Axiom 1 violated! TimeCreatedMs must be MyChannels.MessageCreatedMs!"
            )
        return self
