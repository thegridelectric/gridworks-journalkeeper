"""Type gridworks.event.gt.sh.status, version 000"""

import copy
import json
import logging
from typing import Any, Dict, Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    model_validator,
)
from typing_extensions import Self

from gjk.enums import TelemetryName
from gjk.type_helpers.property_format import (
    LeftRightDotStr,
    UUID4Str,
)
from gjk.types.gt_sh_status import GtShStatus

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GridworksEventGtShStatus(BaseModel):
    """
    This is a gwproto wrapper around a gt.sh.status message that includes the src (which should
    always be the GNodeAlias for the Scada actor), a unique message id (which is immutable once
    the gt.sh.status message is created, and does not change if the SCADA re-sends the message
    due to no ack from AtomicTNode) and a timestamp for when the message was created.
    """

    message_id: UUID4Str
    time_n_s: int
    src: LeftRightDotStr
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
        # Implement check for axiom 1"
        return self

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: Src is Status.FromGNodeAlias and MessageId matches Status.StatusUid.
        Src == Status.FromGNodeAlias
        """
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
    def from_dict(cls, d: dict) -> "GridworksEventGtShStatus":
        d2 = cls.first_season_fix(d)
        for key in d2:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d2)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "GridworksEventGtShStatus":
        try:
            d = json.loads(b)
        except TypeError as e:
            raise GwTypeError("Type must be string or bytes!") from e
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing must result in dict!\n <{b}>")
        return cls.from_dict(d)

    def to_dict(self) -> Dict[str, Any]:
        """
        Handles lists of enums differently than model_dump
        """
        d = self.model_dump(exclude_none=True, by_alias=True)
        d["Status"] = self.status.to_dict()
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the gridworks.event.gt.sh.status.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    @classmethod
    def type_name_value(cls) -> str:
        return "gridworks.event.gt.sh.status"

    @classmethod
    def first_season_fix(cls, d: dict[str, Any]) -> dict[str, Any]:
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
