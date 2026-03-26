from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

# There will only ever be four of these, one with each time_slice value
# Whenever the global stats are recalculate, they'll be replaced

class GlobalStats(Base):
    __tablename__ = "global_stats"
    __table_args__ = (
        CheckConstraint("time_slice IN ('day', 'week', 'month', 'all')"),
    )

    time_slice: Mapped[str] = mapped_column(primary_key=True)
    total_entries: Mapped[int]
    top_content_tag: Mapped[str]
    second_content_tag: Mapped[str]
    top_context_tag: Mapped[str]
    second_context_tag: Mapped[str]
    top_type_tag: Mapped[str]
    second_type_tag: Mapped[str]
    sight_rate: Mapped[float]
    sound_rate: Mapped[float]
    touch_rate: Mapped[float]
    smell_rate: Mapped[float]
    taste_rate: Mapped[float]
    pain_rate: Mapped[float]
    avg_sleep_duration: Mapped[float]