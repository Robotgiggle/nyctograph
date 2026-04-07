from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import Select, select, or_, false, func

from ..models import Tag, ResearchEntry
from ..forms import ResearchFilterForm
from ..utils import ResearcherDep, DbSesDep, flash, not_implemented_yet
from ..jinja import templates

router = APIRouter()

def filter_research_query(query: Select, filters: ResearchFilterForm):
    if filters.content_tags:
        query = query.where(or_(false(), *[ResearchEntry.content_tags.contains(tag) for tag in filters.content_tags]))
    if filters.type_tags:
        query = query.where(or_(false(), *[ResearchEntry.content_tags.contains(tag) for tag in filters.type_tags]))
    if filters.context_tags:
        query = query.where(or_(false(), *[ResearchEntry.content_tags.contains(tag) for tag in filters.context_tags]))

    if filters.date_from:
        query = query.where(ResearchEntry.created_at >= filters.date_from)
    if filters.date_to:
        query = query.where(ResearchEntry.created_at <= filters.date_to)

    if filters.age_min:
        query = query.where(ResearchEntry.user_age >= filters.age_min)
    if filters.age_max:
        query = query.where(ResearchEntry.user_age <= filters.age_max)

    if filters.gender:
        query = query.where(ResearchEntry.user_gender.in_(filters.gender))

    if filters.country:
        query = query.where(ResearchEntry.country == filters.country)
    if filters.state:
        query = query.where(ResearchEntry.state == filters.state)
    if filters.city:
        query = query.where(ResearchEntry.city == filters.city)

    if filters.has_reflection == "yes":
        query = query.where(ResearchEntry.reflection != None)
    elif filters.has_reflection == "no":
        query = query.where(ResearchEntry.reflection == None)

    return query


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

    countQuery = select(func.count()).select_from(ResearchEntry)
    total_count = dbSes.execute(countQuery).scalar()
    match_count = dbSes.execute(filter_research_query(countQuery, current_filters)).scalar()

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