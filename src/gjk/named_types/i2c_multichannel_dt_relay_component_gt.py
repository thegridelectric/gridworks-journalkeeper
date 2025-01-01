"""Type i2c.multichannel.dt.relay.component.gt, version 002"""

from typing import List, Literal, Optional

from gw.named_types import GwBase
from pydantic import StrictInt, field_validator

from gjk.named_types.relay_actor_config import RelayActorConfig
from gjk.property_format import (
    UUID4Str,
)


class I2cMultichannelDtRelayComponentGt(GwBase):
    component_id: UUID4Str
    component_attribute_class_id: UUID4Str
    i2c_address_list: List[StrictInt]
    config_list: List[RelayActorConfig]
    display_name: Optional[str] = None
    hw_uid: Optional[str] = None
    type_name: Literal["i2c.multichannel.dt.relay.component.gt"] = "i2c.multichannel.dt.relay.component.gt"
    version: Literal["002"] = "002"

    @field_validator("config_list")
    @classmethod
    def _check_config_list(cls, v: List[RelayActorConfig]) -> List[RelayActorConfig]:
        return v
