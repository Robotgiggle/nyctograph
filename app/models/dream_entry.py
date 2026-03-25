from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .tag import entry_tag_association_table

if TYPE_CHECKING:
    from . import User, Tag

class DreamEntry(Base):
    __tablename__ = "dream_entries"
    __table_args__ = (
        CheckConstraint("(reflection IS NULL) = (rfln_timestamp IS NULL)"),
    )

    # core entry data
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    description: Mapped[str]
    created_at: Mapped[datetime]
    public: Mapped[bool]
    # additional optional details
    involved_sight: Mapped[bool|None]
    involved_sound: Mapped[bool|None]
    involved_touch: Mapped[bool|None]
    involved_smell: Mapped[bool|None]
    involved_taste: Mapped[bool|None]
    involved_pain: Mapped[bool|None]
    context: Mapped[str|None]
    bed_time: Mapped[datetime|None]
    wake_time: Mapped[datetime|None]
    country: Mapped[str|None]
    state: Mapped[str|None]
    city: Mapped[str|None]
    # follow-up reflection
    reflection: Mapped[str|None]
    rfln_timestamp: Mapped[datetime|None]

    # relations
    user: Mapped[User] = relationship(back_populates="dream_entries")
    tags: Mapped[List[Tag]] = relationship(back_populates="entries", secondary=entry_tag_association_table)

    def __repr__(self) -> str:
        return f"DreamEntry(id: {self.id}, user_id: {self.user_id}, title: {self.title}, desc: {self.description[:30]+'...'})"