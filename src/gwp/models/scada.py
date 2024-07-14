"""
The TaSql ORM object should be made via associated pydantic
class Ta, which includes class validators, using the as_sql method
e.g. msg = Message(...).as_sql()
"""

import logging
from typing import Dict
from typing import Optional
from typing_extensions import Self

from pydantic import BaseModel
from pydantic import field_validator, model_validator
from pydantic.alias_generators import to_pascal
from sqlalchemy import Integer
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

from gwp.models.utils import check_is_left_right_dot
from gwp.models.utils import check_is_reasonable_unix_time_s
from gwp.models.utils import check_is_uuid_canonical_textual


# Define the base class
Base = declarative_base()

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class ScadaSql(Base):
    """
    Make an element of this class via Scada(...).as_sql(),  
    as this will enforce the pydantic validations.

    This is an ORM to track when a SCADA is officially
    live. Data before this point could be the system coming online,
    or even the scada in the lab.

    If start_s is None that means the SCADA is not yet live.

    This is a local hack, as eventually the GNodeId needs to be 
    validated against the GNodeRegistry
    """
    __tablename__ = "messages"
    g_node_id = Column(String, primary_key=True)
    g_node_alias = Column(String, nullable=False)
    short_alias = Column(String, nullable=False)
    start_s = Column(Integer)


class Scada(BaseModel):
    """
    Use Scada(..).as_sql() to create the associated ScadaSql 
    ORM object.

    This is an ORM designed to track when a SCADA is officially
    live. Data before this point could be the system coming online,
    or even the scada in the lab.

    If start_s is None that means the SCADA is not yet live.

    This is a local hack, as eventually the GNodeId needs to be 
    validated against the GNodeRegistry
    """
    g_node_id: str
    g_node_alias: str
    short_alias: str
    start_s: Optional[int]

    class Config:
        populate_by_name = True
        alias_generator = to_pascal
    
    @field_validator("g_node_id")
    def _check_g_node_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"g_node_id failed UuidCanonicalTextual format validation: {e}"
            )
        return v
    
    @field_validator("g_node_alias")
    def _check_g_node_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"g_node_alias failed CheckIsLeftRightDot format validation: {e}"
            )
        return v
    
    @field_validator("time_s")
    def _check_time_s(cls, v: str) -> str:
        if v:
            try:
                check_is_reasonable_unix_time_s(v)
            except ValueError as e:
                raise ValueError(
                    f"time_s failed CheckIsReasonableUnixTimeS format validation: {e}"
                )
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
            )

        if last_word != "scada":
            raise ValueError(
                f"Axiom 1: g_node_alias must end in scada! <{self.g_node_alias}>"
            )
        if self.short_alias != plant:
            raise ValueError(
                f"Axiom 1: short_alias <{self.short_alias}> must be the second to last word in g_node_alias <{self.g_node_alias}>!"
            )
    
    def as_sql(self) -> ScadaSql:
        return ScadaSql(**self.model_dump())
        
        