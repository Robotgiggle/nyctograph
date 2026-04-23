from typing import List, TYPE_CHECKING
from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import DreamEntry, TagTotal, TagAssociation

# extra table to store many-to-many mapping of dream entries to tags
entry_tag_association_table = Table(
    "dream_entry_tags",
    Base.metadata,
    Column("entry_id", ForeignKey("dream_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_val", ForeignKey("tags.value"), primary_key=True),
)

# Represents a common dream attribute within a specific category, and can be linked to a DreamEntry to indicate
# the presence of that attribute in the dream. [REQ-1]
# The database should always contain a fixed set of these, based on the lists found in the build_db script.
class Tag(Base):
    __tablename__ = "tags"

    value: Mapped[str] = mapped_column(primary_key=True)
    category: Mapped[str]

    entries: Mapped[List["DreamEntry"]] = relationship(back_populates="tags", secondary=entry_tag_association_table)
    totals: Mapped[List["TagTotal"]] = relationship(back_populates="tag")

    def __repr__(self) -> str:
        return f"Tag(val: {self.value}, cat: {self.category})"