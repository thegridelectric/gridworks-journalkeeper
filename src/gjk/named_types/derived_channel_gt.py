from typing import Literal

from pydantic import BaseModel

from gjk.enums import GwUnit
from gjk.property_format import (
    LeftRightDot,
    SpaceheatName,
    UUID4Str,
)


class DerivedChannelGt(BaseModel):
    Id: UUID4Str
    Name: SpaceheatName
    CreatedByNodeName: SpaceheatName
    Strategy: SpaceheatName
    OutputUnit: GwUnit | None = None
    DisplayName: str
    TerminalAssetAlias: LeftRightDot
    TypeName: Literal["derived.channel.gt"] = "derived.channel.gt"
    Version: Literal["000"] = "000"
