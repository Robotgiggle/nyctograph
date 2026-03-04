from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import User

class DreamEntry(Base):
    __tablename__ = "dream_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    description: Mapped[str]
    # tags: TODO
    public: Mapped[bool]

    user: Mapped["User"] = relationship(back_populates="dream_entries")

    def __repr__(self) -> str:
        return f"DreamEntry(id: {self.id}, user_id: {self.user_id}, title: {self.title}, desc: {self.description[:30]+'...'})"