"""Type i2c.multichannel.dt.relay.component.gt, version 001"""

from typing import List, Literal, Optional

from gw.named_types import GwBase
from pydantic import StrictInt, field_validator

from gjk.old_types.relay_actor_config_001 import RelayActorConfig001
from gjk.property_format import (
    UUID4Str,
)


class I2cMultichannelDtRelayComponentGt001(GwBase):
    component_id: UUID4Str
    component_attribute_class_id: UUID4Str
    i2c_address_list: List[StrictInt]
    config_list: List[RelayActorConfig001]
    display_name: Optional[str] = None
    hw_uid: Optional[str] = None
    type_name: Literal["i2c.multichannel.dt.relay.component.gt"] = (
        "i2c.multichannel.dt.relay.component.gt"
    )
    version: Literal["001"] = "001"

    @field_validator("config_list")
    @classmethod
    def _check_config_list(
        cls, v: List[RelayActorConfig001]
    ) -> List[RelayActorConfig001]:
        return v
