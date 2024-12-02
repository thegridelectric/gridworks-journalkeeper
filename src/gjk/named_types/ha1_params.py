"""Type ha1.params, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import StrictInt


class Ha1Params(GwBase):
    alpha_times10: StrictInt
    beta_times100: StrictInt
    gamma_ex6: StrictInt
    intermediate_power_kw: float
    intermediate_rswt_f: StrictInt
    dd_power_kw: float
    dd_rswt_f: StrictInt
    dd_delta_t_f: StrictInt
    hp_max_kw_th: float
    type_name: Literal["ha1.params"] = "ha1.params"
    version: Literal["000"] = "000"
