from typing import Literal

from gw.named_types import GwBase


class TankTempCalibration(GwBase):
    depth1_m: float = 1.0
    depth1_b: float = 0.0
    depth2_m: float = 1.0
    depth2_b: float = 0.0
    depth3_m: float = 1.0
    depth3_b: float = 0.0

    type_name: Literal["gw1.tank.temp.calibration"] = "gw1.tank.temp.calibration"
    version: Literal["000"] = "000"
