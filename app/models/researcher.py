from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, List, TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from ..database import Base
from .research_entry import ResearchEntry

if TYPE_CHECKING:
    from . import DownloadRecord


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


def _where_clauses_for_filters(filters: dict[str, Any]) -> list:
    clauses: list = []

    start = parse_iso_date(filters.get("start_date"))
    end = parse_iso_date(filters.get("end_date"))
    if start:
        clauses.append(ResearchEntry.created_at >= datetime.combine(start, datetime.min.time()))
    if end:
        clauses.append(ResearchEntry.created_at <= datetime.combine(end, datetime.max.time()))

    country = (filters.get("country") or "").strip()
    state = (filters.get("state") or "").strip()
    city = (filters.get("city") or "").strip()

    if country:
        clauses.append(ResearchEntry.country == country)
    if state:
        clauses.append(ResearchEntry.state == state)
    if city:
        clauses.append(ResearchEntry.city == city)

    return clauses


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
        return _parse_filters_json(self.data_filters)

    def filter_where_clauses(self) -> list:
        return _where_clauses_for_filters(self.parsed_filters())

    def select_matching_research_entries(
        self,
        *,
        newest_first: bool = False,
        limit: int | None = None,
    ):
        """SELECT over ``research_entries`` view rows this account's saved filters allow."""
        order_col = ResearchEntry.created_at.desc() if newest_first else ResearchEntry.created_at.asc()
        stmt = select(ResearchEntry).order_by(order_col)
        clauses = self.filter_where_clauses()
        if clauses:
            stmt = stmt.where(*clauses)
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

    # TODO: align with filter_where_clauses when viewing a single dream entry by id
    def allowed_to_view(self, entry):
        return True