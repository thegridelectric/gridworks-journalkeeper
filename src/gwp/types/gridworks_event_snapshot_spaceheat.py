"""Type gridworks.event.snapshot.spaceheat, version 000"""

import json
import logging
from typing import Any
from typing import Dict
from typing import Literal

from gw.errors import GwTypeError
from gw.utils import is_pascal_case
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic.alias_generators import to_pascal
from pydantic.alias_generators import to_snake

from gwp.types.snapshot_spaceheat import SnapshotSpaceheat
from gwp.types.snapshot_spaceheat import SnapshotSpaceheat_Maker


LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GridworksEventSnapshotSpaceheat(BaseModel):
    """ """

    message_id: str = Field(
        title="MessageId",
    )
    time_n_s: int = Field(
        title="TimeNS",
    )
    src: str = Field(
        title="Src",
    )
    snap: SnapshotSpaceheat = Field(
        title="Snap",
    )
    type_name: Literal["gridworks.event.snapshot.spaceheat"] = (
        "gridworks.event.snapshot.spaceheat"
    )
    version: Literal["000"] = "000"

    class Config:
        populate_by_name = True
        alias_generator = to_pascal

    @field_validator("message_id")
    def _check_message_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"MessageId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @field_validator("src")
    def _check_src(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(f"Src failed LeftRightDot format validation: {e}")
        return v

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        gridworks.event.snapshot.spaceheat.000 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        gridworks.event.snapshot.spaceheat.000 type. Unlike the standard python dict method,
        it makes the following substantive changes:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.
        """
        d = {
            to_pascal(key): value
            for key, value in self.model_dump().items()
            if value is not None
        }
        d["Snap"] = self.snap.as_dict()
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the gridworks.event.snapshot.spaceheat.000 representation.

        Instances in the class are python-native representations of gridworks.event.snapshot.spaceheat.000
        objects, while the actual gridworks.event.snapshot.spaceheat.000 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is GridworksEventSnapshotSpaceheat.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class GridworksEventSnapshotSpaceheat_Maker:
    type_name = "gridworks.event.snapshot.spaceheat"
    version = "000"

    @classmethod
    def tuple_to_type(cls, tuple: GridworksEventSnapshotSpaceheat) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> GridworksEventSnapshotSpaceheat:
        """
        Given a serialized JSON type object, returns the Python class object.
        """
        try:
            d = json.loads(t)
        except TypeError:
            raise GwTypeError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise GwTypeError(f"Deserializing <{t}> must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> GridworksEventSnapshotSpaceheat:
        """
        Deserialize a dictionary representation of a gridworks.event.snapshot.spaceheat.000 message object
        into a GridworksEventSnapshotSpaceheat python object for internal use.

        This is the near-inverse of the GridworksEventSnapshotSpaceheat.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a GwTypeError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           GwTypeError: if the dict cannot be turned into a GridworksEventSnapshotSpaceheat object.

        Returns:
            GridworksEventSnapshotSpaceheat
        """
        for key in d.keys():
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        d2 = dict(d)
        if "MessageId" not in d2.keys():
            raise GwTypeError(f"dict missing MessageId: <{d2}>")
        if "TimeNS" not in d2.keys():
            raise GwTypeError(f"dict missing TimeNS: <{d2}>")
        if "Src" not in d2.keys():
            raise GwTypeError(f"dict missing Src: <{d2}>")
        if "Snap" not in d2.keys():
            raise GwTypeError(f"dict missing Snap: <{d2}>")
        if not isinstance(d2["Snap"], dict):
            raise GwTypeError(f"Snap <{d2['Snap']}> must be a SnapshotSpaceheat!")
        snap = SnapshotSpaceheat_Maker.dict_to_tuple(d2["Snap"])
        d2["Snap"] = snap
        if "TypeName" not in d2.keys():
            raise GwTypeError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise GwTypeError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret gridworks.event.snapshot.spaceheat version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        d3 = {to_snake(key): value for key, value in d2.items()}
        return GridworksEventSnapshotSpaceheat(**d3)
