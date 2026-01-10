from typing import Literal, Self

from gw.named_types import GwBase
from pydantic import PositiveInt, model_validator

from gjk.named_types.tank_temp_calibration import TankTempCalibration


class TankTempCalibrationMap(GwBase):
    buffer: TankTempCalibration
    tank: dict[PositiveInt, TankTempCalibration]

    type_name: Literal["gw1.tank.temp.calibration.map"] = (
        "gw1.tank.temp.calibration.map"
    )
    version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1:
        - There are between 1 and 6 tanks
        - Tank indices must be contiguous starting at 1
        """
        return self
