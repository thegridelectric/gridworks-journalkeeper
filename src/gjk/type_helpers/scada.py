from typing import Optional

from gw.utils import snake_to_pascal
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing_extensions import Self

from gjk.models import ScadaSql
from gjk.type_helpers.utils import (
    check_is_left_right_dot,
    check_is_reasonable_unix_time_s,
    check_is_uuid_canonical_textual,
)


class Scada(BaseModel):
    """
    Use Scada(..).as_sql() to create the associated ScadaSql
    ORM object.

    This is an ORM designed to track when a SCADA is officially
    live. Data before this point could be the system coming online,
    or even the scada in the lab.

    If scada_installed_s is None that means the SCADA has not yet
    been installed at its location.

    This is a local hack, as eventually the GNodeId needs to be
    validated against the GNodeRegistry
    """

    g_node_id: str
    g_node_alias: str
    short_alias: str
    scada_installed_s: Optional[int]
    ta_fully_installed_s: Optional[int]

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=snake_to_pascal,
    )

    @field_validator("g_node_id")
    @classmethod
    def _check_g_node_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"g_node_id failed UuidCanonicalTextual format validation: {e}"
            ) from e
        return v

    @field_validator("g_node_alias")
    @classmethod
    def _check_g_node_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"g_node_alias failed CheckIsLeftRightDot format validation: {e}"
            ) from e
        return v

    @field_validator("scada_installed_s")
    @classmethod
    def _check_scada_installed_s(cls, v: str) -> str:
        if v:
            try:
                check_is_reasonable_unix_time_s(v)
            except ValueError as e:
                raise ValueError(
                    f"scada_installed_s failed CheckIsReasonableUnixTimeS format validation: {e}"
                ) from e
            return v

    @field_validator("ta_fully_installed_s")
    @classmethod
    def _check_ta_fully_installed_s(cls, v: str) -> str:
        if v:
            try:
                check_is_reasonable_unix_time_s(v)
            except ValueError as e:
                raise ValueError(
                    f"ta_fully_installed failed CheckIsReasonableUnixTimeS format validation: {e}"
                ) from e
            return v

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

    def as_sql(self) -> ScadaSql:
        return ScadaSql(**self.model_dump())
