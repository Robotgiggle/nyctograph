from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import DreamEntry

class User(Base):
    __tablename__ = "users"

    # core account info
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True)
    pw_hash: Mapped[str]
    email: Mapped[str]
    public_enabled: Mapped[bool]
    # additional optional details
    age: Mapped[int|None]
    gender: Mapped[str|None]
    med_conditions: Mapped[str|None]
    country: Mapped[str|None]
    state: Mapped[str|None]
    city: Mapped[str|None]

    dream_entries: Mapped[List[DreamEntry]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id: {self.id}, uname: {self.username})"