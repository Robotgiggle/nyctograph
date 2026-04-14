import json
from datetime import date
from typing import List, TYPE_CHECKING
from sqlalchemy import Select, or_, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .research_entry import ResearchEntry

if TYPE_CHECKING:
    from . import DownloadRecord, DreamEntry

class Researcher(Base):
    __tablename__ = "researchers"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    pw_hash: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    ror_id: Mapped[str]
    data_filters: Mapped[str|None]

    downloads: Mapped[List["DownloadRecord"]] = relationship(back_populates="researcher")

    def filter_query(self, query: Select):
        """Filter a provided query based on this researcher's saved filters."""
        if not self.data_filters: raise RuntimeError("This Researcher does not have any configured filters!")
        
        filters = json.loads(self.data_filters)

        if filters["content_tags"]:
            query = query.where(or_(false(), *[ResearchEntry.content_tags.contains(tag) for tag in filters["content_tags"]]))
        if filters["type_tags"]:
            query = query.where(or_(false(), *[ResearchEntry.content_tags.contains(tag) for tag in filters["type_tags"]]))
        if filters["context_tags"]:
            query = query.where(or_(false(), *[ResearchEntry.content_tags.contains(tag) for tag in filters["context_tags"]]))

        if filters["date_from"]:
            query = query.where(ResearchEntry.created_at >= filters["date_from"])
        if filters["date_to"]:
            query = query.where(ResearchEntry.created_at <= filters["date_to"])

        if filters["age_min"]:
            query = query.where(ResearchEntry.user_age >= filters["age_min"])
        if filters["age_max"]:
            query = query.where(ResearchEntry.user_age <= filters["age_max"])

        if filters["gender"]:
            query = query.where(ResearchEntry.user_gender.in_(filters["gender"]))

        if filters["country"]:
            query = query.where(ResearchEntry.country == filters["country"])
        if filters["state"]:
            query = query.where(ResearchEntry.state == filters["state"])
        if filters["city"]:
            query = query.where(ResearchEntry.city == filters["city"])

        if filters["has_reflection"] == "yes":
            query = query.where(ResearchEntry.reflection != None)
        elif filters["has_reflection"] == "no":
            query = query.where(ResearchEntry.reflection == None)

        return query

    def allowed_to_view(self, entry: "DreamEntry") -> bool:
        """Check whether a DreamEntry matches this researcher's saved filters."""
        if not self.data_filters:
            return True
        filters: dict = json.loads(self.data_filters)

        entry_tag_values = {tag.value for tag in entry.tags}

        # Tag filters: if any tags selected in a category, entry must have at least one
        content_tags = set(filters.get("content_tags", []))
        if content_tags and not entry_tag_values & content_tags:
            return False

        type_tags = set(filters.get("type_tags", []))
        if type_tags and not entry_tag_values & type_tags:
            return False

        context_tags = set(filters.get("context_tags", []))
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
        if gender and entry.user.gender not in gender:
            return False

        # Location
        country = filters.get("country")
        if country and entry.country != country:
            return False
        state = filters.get("state")
        if state and entry.state != state:
            return False
        city = filters.get("city")
        if city and entry.city != city:
            return False

        # Reflection
        has_reflection = filters.get("has_reflection")
        if has_reflection == "yes" and entry.reflection is None:
            return False
        if has_reflection == "no" and entry.reflection is not None:
            return False

        return True
