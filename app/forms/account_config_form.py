from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator

from ..models import User

class AccountConfigForm(BaseModel):
    email: str|None = None
    new_username: Annotated[str, Field(min_length=1)]|None = None
    current_password: str|None = None
    new_password: str|None = None
    public_enabled: bool|None = None
    age: Annotated[int, Field(ge=13)]|None = None
    gender: str|None = None
    med_conditions: str|None = None
    country: str|None = None
    state: str|None = None
    city: str|None = None

    @field_validator("age", mode="before")
    @classmethod
    def empty_string_to_none(cls, input: str|None):
        if input == '': return None
        return input

    @model_validator(mode="after")
    def password_not_empty(self):
        if self.new_password == "" and self.current_password:
            raise ValueError("New password cannot be empty!")
        return self