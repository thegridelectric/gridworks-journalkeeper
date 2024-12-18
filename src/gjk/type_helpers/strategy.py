from typing import Any, Dict

from gw.errors import GwTypeError
from gw.utils import is_pascal_case, snake_to_pascal
from pydantic import BaseModel, ConfigDict, ValidationError

from gjk.enums import Strategy


class Strategy(BaseModel):
    name: Strategy
    description: str

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=snake_to_pascal,
    )

    @classmethod
    def from_dict(cls, d: dict) -> "Strategy":
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
        d["Name"] = d["Name"].value
        return d

    def to_sql_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True)
        d["name"] = d["name"].value
        d.pop("type_name", None)
        d.pop("version", None)
        return d
