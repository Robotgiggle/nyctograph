from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import DreamEntry

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True)
    pw_hash: Mapped[str]
    public_enabled: Mapped[bool]

    dream_entries: Mapped[List["DreamEntry"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id: {self.id}, uname: {self.username!r})"