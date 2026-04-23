from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import Tag, GlobalStats

# Records the total number of entries with the specified tag in the specified category. [REQ-4]
# This could be easily queried on-demand, but with lots of entries that could be very slow.
class TagTotal(Base):
    __tablename__ = "tag_totals"
    __table_args__ = (
        ForeignKeyConstraint(
            ["time_slice","age_bracket"],
            ["global_stats.time_slice","global_stats.age_bracket"]
        ),
    )

    tag_val: Mapped[str] = mapped_column(ForeignKey("tags.value"), primary_key=True)
    tag_cat: Mapped[str]
    time_slice: Mapped[str] = mapped_column(primary_key=True)
    age_bracket: Mapped[str] = mapped_column(primary_key=True)
    total: Mapped[int]

    tag: Mapped["Tag"] = relationship(back_populates="totals")
    stats_obj: Mapped["GlobalStats"] = relationship(back_populates="tag_totals")