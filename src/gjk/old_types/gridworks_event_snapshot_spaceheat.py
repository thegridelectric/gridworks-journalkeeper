"""Type gridworks.event.snapshot.spaceheat, version 000"""

import copy
from typing import Any, Literal

from gw.errors import GwTypeError
from gw.utils import snake_to_pascal
from pydantic import ConfigDict, StrictInt

from gjk.enums import TelemetryName
from gjk.old_types.snapshot_spaceheat_000 import SnapshotSpaceheat000
from gjk.property_format import (
    LeftRightDot,
    UUID4Str,
)
from gjk.types.gw_base import GwBase


class GridworksEventSnapshotSpaceheat(GwBase):
    """
    This is a gwproto wrapper around a gt.sh.status message that includes the src (which should
    always be the GNodeAlias for the Scada actor), a unique message id (which is immutable once
    the gt.sh.status message is created, and does not change if the SCADA re-sends the message
    due to no ack from AtomicTNode) and a timestamp for when the message was created.
    """

    message_id: UUID4Str
    time_n_s: StrictInt
    src: LeftRightDot
    snap: SnapshotSpaceheat000
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
