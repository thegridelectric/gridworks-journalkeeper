"""Type ha1.params, version 001"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import StrictInt


class Ha1Params001(GwBase):
    alpha_times10: StrictInt
    beta_times100: StrictInt
    gamma_ex6: StrictInt
    intermediate_power_kw: float
    intermediate_rswt_f: StrictInt
    dd_power_kw: float
    dd_rswt_f: StrictInt
    dd_delta_t_f: StrictInt
    hp_max_kw_th: float
    max_ewt_f: StrictInt
    type_name: Literal["ha1.params"] = "ha1.params"
    version: Literal["001"] = "001"
