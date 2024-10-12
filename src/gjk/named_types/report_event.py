"""Type report.event, version 000"""

from typing import Literal

from gw.named_types import GwBase
from pydantic import model_validator
from typing_extensions import Self

from gjk.named_types.report import Report
from gjk.property_format import (
    UTCMilliseconds,
    UUID4Str,
)


class ReportEvent(GwBase):
    message_id: UUID4Str
    time_created_ms: UTCMilliseconds
    src: str
    report: Report
    type_name: Literal["report.event"] = "report.event"
    version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Src is Report.FromGNodeAlias, MessageId is Report.Id, TimeCreatedMs is Report.MessageCreatedMs .
        """
        if self.src != self.report.from_g_node_alias:
            raise ValueError(
                f"Axiom 1 violated! src {self.src} must be Report.FromGNodeAlias {self.report.from_g_node_alias}"
            )
        if self.message_id != self.report.id:
            raise ValueError("Axiom 1 violated! MessageId must match Report.Id")
        if self.time_created_ms != self.report.message_created_ms:
            raise ValueError(
                "Axiom 1 violated! TimeCreatedMs must be REport.MessageCreatedMs!"
            )
        return self

        return self
