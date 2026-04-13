from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class StandardSignupForm(BaseModel):
    """Standard user registration (SSDS: informed consent + opt-in for public dream entries)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    username: Annotated[str, Field(min_length=3, max_length=64)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=256)]
    password_confirm: str
    consent_data_storage: Literal["yes"]
    public_opt_in: str | None = None

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self

    @property
    def public_enabled(self) -> bool:
        return self.public_opt_in == "yes"


class ResearchSignupRequestForm(BaseModel):
    """Research account request form (step 1 of the account creation process)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Annotated[str, Field(min_length=3, max_length=64)]
    email: EmailStr
    ror_id: Annotated[str, Field(min_length=3, max_length=512)]
    reason: Annotated[str, Field(min_length=5)]

# class ResearchSignupForm(BaseModel):
#     """Research institution registration (separate account table; ROR ID identifies the organization)."""

#     model_config = ConfigDict(str_strip_whitespace=True)

#     username: Annotated[str, Field(min_length=3, max_length=64)]
#     email: EmailStr
#     password: Annotated[str, Field(min_length=8, max_length=256)]
#     password_confirm: str
#     ror_id: Annotated[str, Field(min_length=3, max_length=512)]
#     consent_data_storage: Literal["yes"]

#     @model_validator(mode="after")
#     def passwords_match(self):
#         if self.password != self.password_confirm:
#             raise ValueError("Passwords do not match")
#         return self
