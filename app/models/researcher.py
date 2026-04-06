import json
from datetime import date
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import DownloadRecord

class Researcher(Base):
    __tablename__ = "researchers"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    pw_hash: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    ror_id: Mapped[str]
    data_filters: Mapped[str|None]

    downloads: Mapped[List["DownloadRecord"]] = relationship(back_populates="researcher")

    def allowed_to_view(self, entry) -> bool:
        """Check whether a DreamEntry matches this researcher's saved filters."""
        if not self.data_filters:
            return True
        filters = json.loads(self.data_filters)

        entry_tag_values = {tag.value for tag in entry.tags}

        # Tag filters: if any tags selected in a category, entry must have at least one
        content_tags = set(filters.get("content_tags") or [])
        if content_tags and not entry_tag_values & content_tags:
            return False

        type_tags = set(filters.get("type_tags") or [])
        if type_tags and not entry_tag_values & type_tags:
            return False

        context_tags = set(filters.get("context_tags") or [])
        if context_tags and not entry_tag_values & context_tags:
            return False

        # Date range
        date_from = filters.get("date_from")
        if date_from and entry.created_at.date() < date.fromisoformat(date_from):
            return False
        date_to = filters.get("date_to")
        if date_to and entry.created_at.date() > date.fromisoformat(date_to):
            return False

        # Age range — exclude entries from users without a birth date if age filter is active
        age_min = filters.get("age_min")
        age_max = filters.get("age_max")
        if age_min is not None or age_max is not None:
            user_age = entry.user.age
            if user_age is None:
                return False
            if age_min is not None and user_age < age_min:
                return False
            if age_max is not None and user_age > age_max:
                return False

        # Gender
        gender = filters.get("gender")
        if gender and entry.user.gender != gender:
            return False

        # Country
        country = filters.get("country")
        if country and entry.country != country:
            return False

        # Reflection
        has_reflection = filters.get("has_reflection")
        if has_reflection == "yes" and entry.reflection is None:
            return False
        if has_reflection == "no" and entry.reflection is not None:
            return False

        return True
