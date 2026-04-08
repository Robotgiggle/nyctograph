from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func

from ..models import Tag, ResearchEntry
from ..forms import ResearchFilterForm
from ..utils import ResearcherDep, DbSesDep, flash, not_implemented_yet
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

@router.get("/research/data")
def research_data_page(request: Request, res: ResearcherDep, dbSes: DbSesDep):
    return not_implemented_yet(request, "/research")