from pydantic import BaseModel


class GwBase(BaseModel):
    type_name: str

    @classmethod
    def from_dict(cls, d: str) -> "GwBase":
        raise NotImplementedError
