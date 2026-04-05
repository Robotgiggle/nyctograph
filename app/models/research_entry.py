from datetime import datetime, date, time
from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

# NOTE: Unlike the other models, this is actually just a mapping for a view that already exists in the DB.
#       The view is created based on the code found in app/research_entries_view.sql.
#       *DO NOT* attempt to create or modify instances of this class.

class ResearchEntry(Base):
    __tablename__ = "research_entries"
    metadata = MetaData()

    title: Mapped[str] = mapped_column(primary_key=True)
    description: Mapped[str]
    content_tags: Mapped[str|None]
    type_tags: Mapped[str|None]

    sense_sight: Mapped[bool|None]
    sense_sound: Mapped[bool|None]
    sense_touch: Mapped[bool|None]
    sense_smell: Mapped[bool|None]
    sense_taste: Mapped[bool|None]
    sense_pain: Mapped[bool|None]
    sense_other: Mapped[bool|None]

    created_at: Mapped[datetime]
    context: Mapped[str|None]
    context_tags: Mapped[str|None]
    bed_time: Mapped[time|None]
    wake_time: Mapped[time|None]
    sleep_hours: Mapped[float|None]
    country: Mapped[str|None]
    state: Mapped[str|None]
    city: Mapped[str|None]
    calc_tags: Mapped[str|None]

    reflection: Mapped[str|None]
    rfln_timestamp: Mapped[datetime|None]

    username: Mapped[str] = mapped_column(primary_key=True)
    user_age: Mapped[float|None]
    user_gender: Mapped[str|None]
    user_med_conditions: Mapped[str|None]

    def __repr__(self) -> str:
        return f"ResearchEntry(title: {self.title}, desc: {self.description[:30]+'...'})"