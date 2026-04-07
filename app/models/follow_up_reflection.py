from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .dream_entry import DreamEntry
    from .user import User


class FollowUpReflection(Base):
    __tablename__ = "follow_up_reflections"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("dream_entries.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    text: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(index=True)

    entry: Mapped["DreamEntry"] = relationship(back_populates="follow_up_reflections")
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("ix_follow_up_reflections_entry_id_created_at", "entry_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"FollowUpReflection(id: {self.id}, entry_id: {self.entry_id}, user_id: {self.user_id})"

