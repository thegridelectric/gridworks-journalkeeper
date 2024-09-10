from typing import Any, Dict

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from gjk.type_helpers.property_format import (
    ReasonableUnixTimeS,
)
from gjk.types.data_channel_gt import DataChannelGt


class NodalHourlyEnergy(BaseModel):
    id: str
    hour_start_s: ReasonableUnixTimeS
    power_channel: DataChannelGt
    watt_hours: int = Field(..., gt=0)

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=snake_to_pascal,
    )

    @field_validator("id")
    @classmethod
    def _check_id(cls, v: str) -> str:
        # To do: validate this format:
        # f"{channel.name}_{hour_start}_{g_node}"
        return v

    @classmethod
    def from_dict(cls, d: dict) -> "DataChannelGt":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    def to_dict(self) -> Dict[str, Any]:
        """
        Handles lists of enums differently than model_dump
        """
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["PowerChannel"] = self.power_channel.to_dict()
        return d

    def to_sql_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["power_channel"] = self.power_channel.to_sql_dict()
        d.pop("type_name", None)
        d.pop("version", None)
        return d
