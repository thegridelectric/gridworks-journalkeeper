"""Type flo.params.house0, version 001"""

from typing import List, Literal, Optional

from gw.named_types import GwBase
from gw.utils import snake_to_pascal
from pydantic import ConfigDict, PositiveInt, StrictInt

from gjk.enums import MarketPriceUnit
from gjk.property_format import (
    LeftRightDot,
    UTCSeconds,
    UUID4Str,
)


class FloParamsHouse0(GwBase):
    g_node_alias: LeftRightDot
    flo_params_uid: UUID4Str
    timezone_str: str
    start_unix_s: UTCSeconds
    num_layers: PositiveInt
    horizon_hours: PositiveInt
    storage_volume_gallons: PositiveInt
    storage_losses_percent: float
    hp_min_elec_kw: float
    hp_max_elec_kw: float
    buffer_available_kwh: float
    house_available_kwh: float
    cop_intercept: float
    cop_oat_coeff: float
    cop_min: float
    cop_min_oat_f: float
    cop_lwt_coeff: float
    initial_top_temp_f: StrictInt
    initial_bottom_temp_f: StrictInt
    hp_is_off: bool
    hp_turn_on_minutes: StrictInt
    lmp_forecast: Optional[List[float]] = None
    initial_thermocline: StrictInt
    dist_price_forecast: Optional[List[float]] = None
    reg_price_forecast: Optional[List[float]] = None
    price_forecast_uid: UUID4Str
    oat_forecast_f: Optional[List[float]] = None
    wind_speed_forecast_mph: Optional[List[float]] = None
    weather_uid: UUID4Str
    alpha_times10: StrictInt
    beta_times100: StrictInt
    gamma_ex6: StrictInt
    intermediate_power_kw: float
    intermediate_rswt_f: StrictInt
    dd_power_kw: float
    dd_rswt_f: StrictInt
    dd_delta_t_f: StrictInt
    max_ewt_f: StrictInt
    price_unit: MarketPriceUnit
    params_generated_s: UTCSeconds
    flo_alias: str
    flo_git_commit: str
    type_name: Literal["flo.params.house0"] = "flo.params.house0"
    version: Literal["002"] = "002"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        extra="allow",
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
    )
