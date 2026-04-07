from typing import List, TYPE_CHECKING
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date

from ..database import Base

if TYPE_CHECKING:
    from . import DreamEntry

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("gender IN ('Male', 'Female', 'Other')"),
    )

    # core account info
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    pw_hash: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    public_enabled: Mapped[bool]
    # additional optional details
    birth_date: Mapped[date|None]
    gender: Mapped[str|None]
    med_conditions: Mapped[str|None]
    country: Mapped[str|None]
    state: Mapped[str|None]
    city: Mapped[str|None]

    dream_entries: Mapped[List["DreamEntry"]] = relationship(back_populates="user")

    @property
    def age(self):
        if self.birth_date is None: return None
        else: return (date.today() - self.birth_date).days / 365.25

    def __repr__(self) -> str:
        return f"User(id: {self.id}, uname: {self.username})"