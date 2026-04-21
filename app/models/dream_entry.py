from typing import List, TYPE_CHECKING
from datetime import datetime, time
from sqlalchemy import ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .tag import entry_tag_association_table

if TYPE_CHECKING:
    from . import User, Tag

class DreamEntry(Base):
    __tablename__ = "dream_entries"
    __table_args__ = (
        CheckConstraint("(reflection IS NULL) = (rfln_timestamp IS NULL)"),
        UniqueConstraint("user_id", "title")
    )

    # core entry data
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str]
    description: Mapped[str]
    created_at: Mapped[datetime]
    public: Mapped[bool] = mapped_column(index=True)
    # additional optional details
    sense_sight: Mapped[bool|None]
    sense_sound: Mapped[bool|None]
    sense_touch: Mapped[bool|None]
    sense_smell: Mapped[bool|None]
    sense_taste: Mapped[bool|None]
    sense_pain: Mapped[bool|None]
    sense_other: Mapped[bool|None]
    context: Mapped[str|None]
    bed_time: Mapped[time|None]
    wake_time: Mapped[time|None]
    sleep_hours: Mapped[float|None]
    country: Mapped[str|None]
    state: Mapped[str|None]
    city: Mapped[str|None]
    # follow-up reflection
    reflection: Mapped[str|None]
    rfln_timestamp: Mapped[datetime|None]

    # relations
    user: Mapped["User"] = relationship(back_populates="dream_entries")
    tags: Mapped[List["Tag"]] = relationship(
        back_populates="entries", 
        secondary=entry_tag_association_table, 
        cascade="all",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"DreamEntry(id: {self.id}, user_id: {self.user_id}, title: {self.title}, desc: {self.description[:30]+'...'})"