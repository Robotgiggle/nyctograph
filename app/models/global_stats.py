from typing import TYPE_CHECKING, List
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import TagTotal, TagAssociation

# There will only ever be sixteen of these, one with each combination of time_slice and age_bracket
# Whenever the global stats are recalculated, they'll be replaced

class GlobalStats(Base):
    __tablename__ = "global_stats"
    __table_args__ = (
        CheckConstraint("time_slice IN ('day', 'week', 'month', 'all')"),
        CheckConstraint("age_bracket IN ('13-29', '30-49', '50+', 'all')"),
    )

    time_slice: Mapped[str] = mapped_column(primary_key=True)
    age_bracket: Mapped[str] = mapped_column(primary_key=True)
    total_entries: Mapped[int]
    sight_rate: Mapped[float]
    sound_rate: Mapped[float]
    touch_rate: Mapped[float]
    smell_rate: Mapped[float]
    taste_rate: Mapped[float]
    pain_rate: Mapped[float]
    other_rate: Mapped[float]
    avg_sleep_duration: Mapped[float]

    tag_totals: Mapped[List["TagTotal"]] = relationship(back_populates="stats_obj")
    tag_associations: Mapped[List["TagAssociation"]] = relationship(back_populates="stats_obj")