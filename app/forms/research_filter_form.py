from typing import List, Literal
from pydantic import BaseModel, field_validator
from datetime import date


class ResearchFilterForm(BaseModel):
    content_tags: List[str] = []
    type_tags: List[str] = []
    context_tags: List[str] = []
    date_from: date | None = None
    date_to: date | None = None
    age_min: int | None = None
    age_max: int | None = None
    gender: str | None = None
    country: str | None = None
    has_reflection: Literal["yes", "no"] | None = None

    @field_validator("date_from", "date_to", "gender", "country", "age_min", "age_max", "has_reflection", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if v == "":
            return None
        return v

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str | None) -> "ResearchFilterForm":
        if not data:
            return cls()
        return cls.model_validate_json(data)
