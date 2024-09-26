"""Type gridworks.event.snapshot.spaceheat, version 000"""

import copy
import json
from typing import Any, Dict, Literal

from gw.errors import GwTypeError
from gw.utils import recursively_pascal, snake_to_pascal
from pydantic import BaseModel, ConfigDict, StrictInt, ValidationError

from gjk.enums import TelemetryName
from gjk.property_format import (
    LeftRightDot,
    UUID4Str,
)
from gjk.types.snapshot_spaceheat import SnapshotSpaceheat


class GridworksEventSnapshotSpaceheat(BaseModel):
    """
    This is a gwproto wrapper around a gt.sh.status message that includes the src (which should
    always be the GNodeAlias for the Scada actor), a unique message id (which is immutable once
    the gt.sh.status message is created, and does not change if the SCADA re-sends the message
    due to no ack from AtomicTNode) and a timestamp for when the message was created.
    """

    message_id: UUID4Str
    time_n_s: StrictInt
    src: LeftRightDot
    snap: SnapshotSpaceheat
    type_name: Literal["gridworks.event.snapshot.spaceheat"] = (
        "gridworks.event.snapshot.spaceheat"
    )
    version: Literal["000"] = "000"

    model_config = ConfigDict(
        alias_generator=snake_to_pascal,
        frozen=True,
        populate_by_name=True,
    )

    @classmethod
    def first_season_fix(cls, d: dict[str, Any]) -> dict[str, Any]:
        """
        Makes key "snap" -> "Snap", following the rule that
        all GridWorks types must have PascalCase keys
        """

        d2 = copy.deepcopy(d)

        if "snap" in d2.keys():
            d2["Snap"] = d2["snap"]
            del d2["snap"]

        if "Snap" not in d2.keys():
            raise GwTypeError(f"dict missing Snap: <{d2.keys()}>")

        if "Snapshot" not in d2["Snap"].keys():
            raise GwTypeError(f"dict['Snap'] missing Snapshot: <{d2['Snap'].keys()}>")

        snapshot = d2["Snap"]["Snapshot"]
        # replace values with symbols for TelemetryName in SimpleTelemetryList
        if "TelemetryNameList" not in snapshot.keys():
            raise Exception(
                f"Snapshot does not have TelemetryNameList in keys! simple.key()): <{snapshot.keys()}>"
            )
        telemetry_name_list = snapshot["TelemetryNameList"]
        new_list = []
        for tn in telemetry_name_list:
            new_list.append(TelemetryName.value_to_symbol(tn))
        snapshot["TelemetryNameList"] = new_list

        d2["Snap"]["Snapshot"] = snapshot
        d2["Version"] = "000"
        return d2

    @classmethod
    def from_dict(cls, d: dict) -> "GridworksEventSnapshotSpaceheat":
        d2 = cls.first_season_fix(d)
        if not recursively_pascal(d2):
            raise GwTypeError(f"Not recursively PascalCase: {d2}")
        try:
            t = cls(**d2)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    @classmethod
    def from_type(cls, b: bytes) -> "GridworksEventSnapshotSpaceheat":
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
        d["Snap"] = self.snap.to_dict()
        return d

    def to_type(self) -> bytes:
        """
        Serialize to the gridworks.event.snapshot.spaceheat.000 representation designed to send in a message.
        """
        json_string = json.dumps(self.to_dict())
        return json_string.encode("utf-8")

    @classmethod
    def type_name_value(cls) -> str:
        return "gridworks.event.snapshot.spaceheat"
