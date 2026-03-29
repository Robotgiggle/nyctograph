from typing import List, TYPE_CHECKING
from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import DreamEntry

# extra table to store many-to-many mapping of dream entries to tags
entry_tag_association_table = Table(
    "dream_entry_tags",
    Base.metadata,
    Column("entry_id", ForeignKey("dream_entries.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str]
    value: Mapped[str]

    entries: Mapped[List["DreamEntry"]] = relationship(back_populates="tags", secondary=entry_tag_association_table)

    def __repr__(self) -> str:
        return f"Tag(id: {self.id}, cat: {self.category}, val: {self.value})"