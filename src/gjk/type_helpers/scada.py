from typing import Any, Dict, Optional

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from typing_extensions import Self

from gjk.property_format import (
    LeftRightDot,
    UTCSeconds,
    UUID4Str,
)


class Scada(BaseModel):
    """
    This is an ORM designed to track when a SCADA is officially
    live. Data before this point could be the system coming online,
    or even the scada in the lab.

    If scada_installed_s is None that means the SCADA has not yet
    been installed at its location.

    This is a local hack, as eventually the GNodeId needs to be
    validated against the GNodeRegistry
    """

    g_node_id: UUID4Str
    g_node_alias: LeftRightDot
    short_alias: str
    scada_installed_s: Optional[UTCSeconds]
    ta_fully_installed_s: Optional[UTCSeconds]

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=snake_to_pascal,
    )

    @model_validator(mode="after")
    def _check_axiom_1(self) -> Self:
        """
        short_alias must be the second to last word in g_node_alias
        and g_node_alias ends in .scada

        Example: beech and hw1.isone.me.versant.keene.beech.scada
        """
        try:
            last_word = self.g_node_alias.split(".")[-1]
            plant = self.g_node_alias.split(".")[-2]
        except IndexError as e:
            raise ValueError(
                f"Axiom 1: g_node_alias must end in scada! <{self.g_node_alias}>"
            ) from e

        if last_word != "scada":
            raise ValueError(
                f"Axiom 1: g_node_alias must end in scada! <{self.g_node_alias}>"
            )
        if self.short_alias != plant:
            raise ValueError(
                f"Axiom 1: short_alias <{self.short_alias}> must be the second to last word in g_node_alias <{self.g_node_alias}>!"
            )
        return self

    @classmethod
    def from_dict(cls, d: dict) -> "Scada":
        for key in d:
            if not is_pascal_case(key):
                raise GwTypeError(f"Key '{key}' is not PascalCase")
        try:
            t = cls(**d)
        except ValidationError as e:
            raise GwTypeError(f"Pydantic validation error: {e}") from e
        return t

    def to_dict(self) -> Dict[str, Any]:
        """
        Handles lists of enums differently than model_dump
        """
        d = self.model_dump(exclude_none=True, by_alias=True)
        return d
