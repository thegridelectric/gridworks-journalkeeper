"""Type flo.params.house0, version 000"""

from typing import List, Literal, Optional

from gw.named_types import GwBase
from pydantic import PositiveInt, StrictInt

from gjk.enums import MarketPriceUnit
from gjk.property_format import (
    LeftRightDot,
    UTCSeconds,
    UUID4Str,
)


class FloParamsHouse0_000(GwBase):
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
    cop_intercept: float
    cop_oat_coeff: float
    cop_lwt_coeff: float
    initial_top_temp_f: StrictInt
    initial_thermocline: StrictInt
    lmp_forecast: Optional[List[float]] = None
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
    type_name: Literal["flo.params.house0"] = "flo.params.house0"
    version: Literal["000"] = "000"
