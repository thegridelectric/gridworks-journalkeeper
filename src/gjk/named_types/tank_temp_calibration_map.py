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
        tank_indices = sorted(self.tank.keys())

        num_tanks = len(tank_indices)
        if num_tanks < 1 or num_tanks > 6:
            raise ValueError(
                f"Axiom 1 failed: expected between 1 and 6 tanks, got {num_tanks}"
            )

        expected_indices = list(range(1, num_tanks + 1))
        if tank_indices != expected_indices:
            raise ValueError(
                "Axiom 1 failed: tank indices must be contiguous starting at 1. "
                f"Expected {expected_indices}, got {tank_indices}"
            )

        return self
