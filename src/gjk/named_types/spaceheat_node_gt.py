"""Type spaceheat.node.gt, version 200"""

from typing import Literal, Optional, Self

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import ConfigDict, StrictInt, model_validator

from gjk.enums import ActorClass
from gjk.property_format import (
    HandleName,
    SpaceheatName,
    UUID4Str,
)


class SpaceheatNodeGt(GwBase):
    name: SpaceheatName
    actor_hierarchy_name: HandleName | None = None
    handle: HandleName | None = None
    actor_class: ActorClass
    display_name: str | None = None
    component_id_id: str | None = None
    nameplate_power_w: StrictInt | None = None
    in_power_metering: bool | None = None
    sh_node_id: UUID4Str
    type_name: Literal["spaceheat.node.gt"] = "spaceheat.node.gt"
    version: Literal["200"] = "200"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: InPowerMetering requirements.
        If InPowerMetering exists and is true, then NameplatePowerW must exist
        """
        if self.in_power_metering and self.nameplate_power_w is None:
            raise ValueError(
                "Axiom 1 failed! "
                "If InPowerMetering exists and is true, then NameplatePowerW must exist"
            )
        return self
