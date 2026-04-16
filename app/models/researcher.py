from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, List, TYPE_CHECKING

from sqlalchemy import Select, false, or_, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from ..database import Base
from .research_entry import ResearchEntry

if TYPE_CHECKING:
    from . import DownloadRecord, DreamEntry


def parse_iso_date(s: str | None) -> date | None:
    s = (s or "").strip()
    if not s:
        return None
    return date.fromisoformat(s)


def _parse_filters_json(filters_json: str | None) -> dict[str, Any]:
    if not filters_json:
        return {}
    try:
        obj = json.loads(filters_json)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _normalize_filter_dict(filters: dict[str, Any]) -> dict[str, Any]:
    """Merge legacy research_data keys (start_date/end_date) with main ResearchFilterForm keys."""
    out = dict(filters)
    if out.get("date_from") in (None, "") and out.get("start_date"):
        out["date_from"] = out.pop("start_date", None)
    if out.get("date_to") in (None, "") and out.get("end_date"):
        out["date_to"] = out.pop("end_date", None)
    for key, default in (
        ("content_tags", []),
        ("type_tags", []),
        ("context_tags", []),
    ):
        if key not in out or out[key] is None:
            out[key] = default
    return out


def _date_to_datetime_start(d: date | str | None):
    if d is None or d == "":
        return None
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return datetime.combine(d, datetime.min.time())


def _date_to_datetime_end(d: date | str | None):
    if d is None or d == "":
        return None
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return datetime.combine(d, datetime.max.time())


class Researcher(Base):
    __tablename__ = "researchers"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    pw_hash: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    ror_id: Mapped[str]
    data_filters: Mapped[str|None]

    downloads: Mapped[List["DownloadRecord"]] = relationship(back_populates="researcher")

    def parsed_filters(self) -> dict[str, Any]:
        return _normalize_filter_dict(_parse_filters_json(self.data_filters))

    def filter_query(self, query: Select):
        """Filter a query on ``ResearchEntry`` using this account's saved filters (same rules as /research UI)."""
        if not self.data_filters:
            raise RuntimeError("This Researcher does not have any configured filters!")

        filters = self.parsed_filters()

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

        df = filters.get("date_from")
        dt = filters.get("date_to")
        d_start = _date_to_datetime_start(df) if df not in (None, "") else None
        d_end = _date_to_datetime_end(dt) if dt not in (None, "") else None
        if d_start:
            query = query.where(ResearchEntry.created_at >= d_start)
        if d_end:
            query = query.where(ResearchEntry.created_at <= d_end)

        age_min = filters.get("age_min")
        age_max = filters.get("age_max")
        if age_min is not None:
            query = query.where(ResearchEntry.user_age >= age_min)
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

    def select_matching_research_entries(
        self,
        *,
        newest_first: bool = False,
        limit: int | None = None,
    ):
        """SELECT over ``research_entries`` using the same rules as ``filter_query``."""
        if not self.data_filters:
            return select(ResearchEntry).where(false())

        stmt = select(ResearchEntry)
        stmt = self.filter_query(stmt)
        order_col = ResearchEntry.created_at.desc() if newest_first else ResearchEntry.created_at.asc()
        stmt = stmt.order_by(order_col)
        if limit is not None:
            stmt = stmt.limit(limit)
        return stmt

    def fetch_matching_research_entries(
        self,
        session: Session,
        *,
        newest_first: bool = False,
        limit: int | None = None,
    ) -> list[ResearchEntry]:
        stmt = self.select_matching_research_entries(newest_first=newest_first, limit=limit)
        return list(session.scalars(stmt).all())

    def allowed_to_view(self, entry: "DreamEntry") -> bool:
        """Check whether a DreamEntry matches this researcher's saved filters."""
        if not self.data_filters:
            return True

        filters = self.parsed_filters()
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
