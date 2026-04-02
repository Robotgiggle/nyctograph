from typing import Annotated, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date, timedelta

from ..models import User

class AccountConfigForm(BaseModel):
    email: str|None = None
    new_username: Annotated[str, Field(min_length=1)]|None = None
    current_password: str|None = None
    new_password: str|None = None
    public_enabled: bool|None = None
    birth_date: date|Literal['']|None = None
    gender: str|None = None
    med_conditions: str|None = None
    country: str|None = None
    state: str|None = None
    city: str|None = None

    @field_validator("birth_date")
    @classmethod
    def must_be_at_least_13(cls, input):
        if type(input) is date:
            age = date.today() - input
            if age.days/365.25 < 13:
                raise ValueError("Must be at least 13 years old!")
        return input

    @model_validator(mode="after")
    def password_not_empty(self):
        if self.new_password == "" and self.current_password:
            raise ValueError("New password cannot be empty!")
        return self