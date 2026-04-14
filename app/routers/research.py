import math
from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func

from ..models import Tag, ResearchEntry
from ..forms import ResearchFilterForm
from ..utils import ResearcherDep, DbSesDep, flash
from ..jinja import templates

router = APIRouter()

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

    if res.data_filters:
        countQuery = select(func.count()).select_from(ResearchEntry)
        matchQuery = res.filter_query(countQuery)
        total_count = dbSes.execute(countQuery).scalar()
        match_count = dbSes.execute(matchQuery).scalar()
    else:
        total_count = match_count = None

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

def _page_range(page: int, total_pages: int) -> list[int]:
    """Return page numbers to display, using -1 as an ellipsis marker."""
    if total_pages <= 7:
        return list(range(1, total_pages + 1))
    pages: list[int] = [1]
    if page > 3:
        pages.append(-1)
    for p in range(max(2, page - 1), min(total_pages, page + 2)):
        pages.append(p)
    if page < total_pages - 2:
        pages.append(-1)
    if total_pages not in pages:
        pages.append(total_pages)
    return pages


@router.get("/research/data")
def research_data_page(
    request: Request,
    res: ResearcherDep,
    dbSes: DbSesDep,
    page: int = 1,
    per_page: int = 10,
):
    if not res:
        flash(request, "This page requires a research account.", "warn")
        return RedirectResponse("/login", status_code=303)

    if not res.data_filters:
        flash(request, "Please configure your research filters before viewing data.", "warn")
        return RedirectResponse("/research", status_code=303)

    if per_page not in (10, 25, 50):
        per_page = 10

    count_query = res.filter_query(select(func.count()).select_from(ResearchEntry))
    total_count = dbSes.execute(count_query).scalar() or 0

    total_pages = max(1, math.ceil(total_count / per_page))
    page = max(1, min(page, total_pages))

    entries_query = res.filter_query(select(ResearchEntry))
    entries_query = entries_query.offset((page - 1) * per_page).limit(per_page)
    entries = dbSes.execute(entries_query).scalars().all()

    return templates.TemplateResponse(request, "research-data.html", {
        "entries": entries,
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "page_range": _page_range(page, total_pages),
    })