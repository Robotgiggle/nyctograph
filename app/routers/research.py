from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..models import Tag, ResearchEntry
from ..forms import ResearchFilterForm
from ..utils import ResearcherDep, DbSesDep, flash
from ..jinja import templates

router = APIRouter()


def _entry_matches_filters(filters: ResearchFilterForm, entry: ResearchEntry) -> bool:
    """Apply filter criteria to a ResearchEntry (tags stored as semicolon-separated strings)."""
    entry_content_tags = set(entry.content_tags.split(";")) if entry.content_tags else set()
    entry_type_tags = set(entry.type_tags.split(";")) if entry.type_tags else set()
    entry_context_tags = set(entry.context_tags.split(";")) if entry.context_tags else set()

    if filters.content_tags and not entry_content_tags & set(filters.content_tags):
        return False
    if filters.type_tags and not entry_type_tags & set(filters.type_tags):
        return False
    if filters.context_tags and not entry_context_tags & set(filters.context_tags):
        return False

    if filters.date_from and entry.created_at.date() < filters.date_from:
        return False
    if filters.date_to and entry.created_at.date() > filters.date_to:
        return False

    if filters.age_min is not None or filters.age_max is not None:
        if entry.user_age is None:
            return False
        if filters.age_min is not None and entry.user_age < filters.age_min:
            return False
        if filters.age_max is not None and entry.user_age > filters.age_max:
            return False

    if filters.gender and entry.user_gender not in filters.gender:
        return False

    if filters.country and entry.country != filters.country:
        return False
    if filters.state and entry.state != filters.state:
        return False
    if filters.city and entry.city != filters.city:
        return False

    if filters.has_reflection == "yes" and entry.reflection is None:
        return False
    if filters.has_reflection == "no" and entry.reflection is not None:
        return False

    return True


@router.get("/research")
def research_filter_page(request: Request, res: ResearcherDep, dbSes: DbSesDep):
    if not res:
        flash(request, "This page requires a research account.", "warn")
        return RedirectResponse("/login", status_code=303)

    current_filters = ResearchFilterForm.from_json(res.data_filters)

    all_tags = dbSes.execute(select(Tag)).scalars().all()
    content_tags = [t.value for t in all_tags if t.category == "dream_content"]
    type_tags = [t.value for t in all_tags if t.category == "dream_type"]
    context_tags = [t.value for t in all_tags if t.category == "irl_context"]

    all_entries = dbSes.execute(select(ResearchEntry)).scalars().all()
    match_count = sum(1 for e in all_entries if _entry_matches_filters(current_filters, e))
    total_count = len(all_entries)

    return templates.TemplateResponse(request, "research.html", {
        "filters": current_filters,
        "content_tags": content_tags,
        "type_tags": type_tags,
        "context_tags": context_tags,
        "match_count": match_count,
        "total_count": total_count,
    })


@router.post("/research")
def research_filter_action(
    request: Request,
    res: ResearcherDep,
    dbSes: DbSesDep,
    formData: Annotated[ResearchFilterForm, Form()],
):
    if not res:
        flash(request, "This page requires a research account.", "warn")
        return RedirectResponse("/login", status_code=303)

    res.data_filters = formData.to_json()
    dbSes.commit()
    flash(request, "Filters saved.", "success")
    return RedirectResponse("/research", status_code=303)
