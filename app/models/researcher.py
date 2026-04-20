from __future__ import annotations

import json
from datetime import date, time, datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Select, CheckConstraint, false, or_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .research_entry import ResearchEntry

if TYPE_CHECKING:
    from . import DataAccessRecord, DreamEntry


def date_str_to_datetime(d: str, max: bool):
    theDate = date.fromisoformat(d[:10])
    return datetime.combine(theDate, time.max if max else time.min)


class Researcher(Base):
    __tablename__ = "researchers"
    __table_args__ = (
        CheckConstraint("data_request_status IN ('Pending', 'Fulfilled')"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    pw_hash: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    ror_id: Mapped[str]
    inst_name: Mapped[str]
    pending_filters: Mapped[str|None]
    data_filters: Mapped[str|None]
    data_request_status: Mapped[str|None]

    data_accesses: Mapped[List["DataAccessRecord"]] = relationship(back_populates="researcher")

    def get_last_access_dt(self):
        """Get the timestamp of the latest data access request."""
        if not self.data_accesses: return None
        latest = datetime.min
        for access in self.data_accesses:
            if access.accessed_at > latest:
                latest = access.accessed_at
        return latest

    def filter_query(self, query: Select, pending: bool = False):
        """Filter a query on ``ResearchEntry`` using this account's saved filters (same rules as /research UI)."""
        filtersRaw = self.pending_filters if pending else self.data_filters
        if not filtersRaw:
            raise RuntimeError("This Researcher does not have any configured filters!")
        filters: dict = json.loads(filtersRaw)

        # When filtering a real query, only entries that existed when the filters were locked in
        # should be accessible. This prevents future entries from being included without the
        # knowledge of their creators.
        if not pending:
            last_access = self.get_last_access_dt()
            if last_access:
                query = query.where(ResearchEntry.created_at <= last_access)

        content_tags = filters.get("content_tags") or []
        if content_tags:
            query = query.where(
                or_(false(), *[ResearchEntry.content_tags.contains(tag) for tag in content_tags])
            )
        type_tags = filters.get("type_tags") or []
        if type_tags:
            query = query.where(
                or_(false(), *[ResearchEntry.type_tags.contains(tag) for tag in type_tags])
            )
        context_tags = filters.get("context_tags") or []
        if context_tags:
            query = query.where(
                or_(false(), *[ResearchEntry.context_tags.contains(tag) for tag in context_tags])
            )

        date_from = filters.get("date_from")
        if date_from:
            dt_from = date_str_to_datetime(date_from, max=False)
            query = query.where(ResearchEntry.created_at >= dt_from)
        date_to = filters.get("date_to")
        if date_to:
            dt_to = date_str_to_datetime(date_to, max=True)
            query = query.where(ResearchEntry.created_at <= dt_to)

        age_min = filters.get("age_min")
        if age_min is not None:
            query = query.where(ResearchEntry.user_age >= age_min)
        age_max = filters.get("age_max")
        if age_max is not None:
            query = query.where(ResearchEntry.user_age <= age_max)

        gender = filters.get("gender")
        if gender:
            query = query.where(ResearchEntry.user_gender.in_(gender))

        country = filters.get("country")
        if country:
            query = query.where(ResearchEntry.country == country)
        state = filters.get("state")
        if state:
            query = query.where(ResearchEntry.state == state)
        city = filters.get("city")
        if city:
            query = query.where(ResearchEntry.city == city)

        has_reflection = filters.get("has_reflection")
        if has_reflection == "yes":
            query = query.where(ResearchEntry.reflection.is_not(None))
        elif has_reflection == "no":
            query = query.where(ResearchEntry.reflection.is_(None))

        return query

    def allowed_to_view(self, entry: "DreamEntry") -> bool:
        """Check whether a DreamEntry matches this researcher's saved filters."""
        if not self.data_filters:
            return True

        filters = json.loads(self.data_filters)
        entry_tag_values = {tag.value for tag in entry.tags}

        content_tags = set(filters.get("content_tags") or [])
        if content_tags and not entry_tag_values & content_tags:
            return False

        type_tags = set(filters.get("type_tags") or [])
        if type_tags and not entry_tag_values & type_tags:
            return False

        context_tags = set(filters.get("context_tags") or [])
        if context_tags and not entry_tag_values & context_tags:
            return False

        date_from = filters.get("date_from")
        if date_from and entry.created_at.date() < date.fromisoformat(str(date_from)[:10]):
            return False
        date_to = filters.get("date_to")
        if date_to and entry.created_at.date() > date.fromisoformat(str(date_to)[:10]):
            return False

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

        gender = filters.get("gender")
        if gender and entry.user.gender not in gender:
            return False

        country = filters.get("country")
        if country and entry.country != country:
            return False
        state = filters.get("state")
        if state and entry.state != state:
            return False
        city = filters.get("city")
        if city and entry.city != city:
            return False

        has_reflection = filters.get("has_reflection")
        if has_reflection == "yes" and entry.reflection is None:
            return False
        if has_reflection == "no" and entry.reflection is not None:
            return False

        return True
