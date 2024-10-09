"""Type gridworks.event.gt.sh.status, version 000"""

import copy
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import snake_to_pascal
from pydantic import ConfigDict, StrictInt, model_validator
from typing_extensions import Self

from gjk.enums import TelemetryName
from gjk.old_types.gt_sh_status import GtShStatus
from gjk.property_format import (
    LeftRightDot,
    UUID4Str,
)
from gjk.types.gw_base import GwBase


class GridworksEventGtShStatus(GwBase):
    message_id: UUID4Str
    time_n_s: StrictInt
    src: LeftRightDot
    status: GtShStatus
    type_name: Literal["gridworks.event.gt.sh.status"] = "gridworks.event.gt.sh.status"
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        frozen=True,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: SCADA time consistency.
        SlotStartS + ReportingPeriodS < MessageCreatedS (which is TimeNS / 10**9)
        """
        # a = self.status.slot_start_unix_s + self.status.reporting_period_s
        # b = self.time_n_s / 10**9
        # if a > b:
        #     raise ValueError(
        #         f"slot_start + reporting_period was larger than message created time!: {self.message_id}"
        #     )
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: Src is Status.FromGNodeAlias and MessageId matches Status.StatusUid.
        Src == Status.FromGNodeAlias
        """
        if self.src != self.status.from_g_node_alias:
            raise ValueError(
                f"self.src <{self.src}> must be status.from_g_node_alias <{self.status.from_g_node_alias}>"
            )

        if self.message_id != self.status.status_uid:
            raise ValueError(
                f"message_id <{self.message_id}> must be status.status_uid <{self.status.status_uid}>"
            )

        return self

    @classmethod
    def first_season_fix(cls, d: dict) -> dict:
        """
        Makes key "status" -> "Status", following the rule that
        all GridWorks types must have PascalCase keys
        """

        d2 = copy.deepcopy(d)
        if "status" in d2.keys():
            d2["Status"] = d2["status"]
            del d2["status"]
        if "Status" not in d2.keys():
            raise GwTypeError(f"dict missing Status: <{d2}>")

        status = d2["Status"]

        # replace values with symbols for TelemetryName in SimpleTelemetryList
        simple_list = status["SimpleTelemetryList"]
        for simple in simple_list:
            if "TelemetryName" not in simple.keys():
                raise Exception(
                    f"simple does not have TelemetryName in keys! simple.key()): <{simple.keys()}>"
                )
            simple["TelemetryNameGtEnumSymbol"] = TelemetryName.value_to_symbol(
                simple["TelemetryName"]
            )
            del simple["TelemetryName"]
        status["SimpleTelemetryList"] = simple_list

        # replace values with symbols for TelemetryName in MultipurposeTelemetryList
        multi_list = status["MultipurposeTelemetryList"]
        for multi in multi_list:
            multi["TelemetryNameGtEnumSymbol"] = TelemetryName.value_to_symbol(
                multi["TelemetryName"]
            )
            del multi["TelemetryName"]
        status["MultipurposeTelemetryList"] = multi_list

        orig_message_id = d2["MessageId"]
        if orig_message_id != status["StatusUid"]:
            d2["MessageId"] = status["StatusUid"]

        d2["Status"] = status
        d2["Version"] = "000"
        return d2
