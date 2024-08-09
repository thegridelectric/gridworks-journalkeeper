from gw.utils import snake_to_pascal
from pydantic import BaseModel, field_validator

from gjk.enums import TelemetryName
from gjk.models import NodalHourlyEnergySql
from gjk.type_helpers.utils import (
    check_is_reasonable_unix_time_s,
    check_is_uuid_canonical_textual,
)
from gjk.types.data_channel_gt import DataChannelGt


class NodalHourlyEnergy(BaseModel):
    id: str
    hour_start_s: int
    power_channel: DataChannelGt
    watt_hours: int

    class Config:
        populate_by_name = True
        alias_generator = snake_to_pascal

    @field_validator("id")
    @classmethod
    def _check_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"id failed UuidCanonicalTextual format validation: {e}"
            ) from e
        return v

    @field_validator("hour_start_s")
    @classmethod
    def _check_hour_start_s(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_s(v)
        except ValueError as e:
            raise ValueError(
                f"from_alias failed CheckIsLeftRightDot format validation: {e}"
            ) from e
        return v

    @field_validator("power_channel")
    @classmethod
    def _check_power_channel(cls, v: DataChannelGt) -> DataChannelGt:
        if v.telemetry_name != TelemetryName.PowerW:
            raise ValueError(
                f"Not entering {v.name} data - uses {v.telemetry_name.value} and"
                " needs to use PowerW"
            )
        try:
            check_is_reasonable_unix_time_s(v)
        except ValueError as e:
            raise ValueError(
                f"from_alias failed CheckIsLeftRightDot format validation: {e}"
            ) from e
        return v

    @field_validator("watt_hours")
    @classmethod
    def _check_watt_hours(cls, v: int) -> int:
        if v < 0:
            raise ValueError(
                "This table is in the thought domain of data analysis for electricity "
                "used by heat pump thermal storage heating systems. This number "
                f"must be positive: {v}"
            )
        return v

    def as_sql(self) -> NodalHourlyEnergySql:
        return NodalHourlyEnergySql(**self.model_dump())
