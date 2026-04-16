import math
import csv
import io
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import select, func
from datetime import datetime

from ..models import Tag, ResearchEntry, DownloadRecord
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


@router.get("/research/download")
def research_download_page(request: Request, dbSes: DbSesDep, res: ResearcherDep):
    if not res:
        flash(request, "This page requires a research institution account.", "warn")
        return RedirectResponse("/login", status_code=303)

    if not res.data_filters:
        flash(request, "No requested data. Set filters first.", "warn")
        return templates.TemplateResponse(request, "download-requested-data.html", {"has_data": False})

    rows = res.fetch_matching_research_entries(dbSes, newest_first=False, limit=None)
    if not rows:
        flash(request, "No public entries match your current filters.", "warn")
        return templates.TemplateResponse(request, "download-requested-data.html", {"has_data": False})

    csv_bytes = _generate_csv_bytes(rows)
    return templates.TemplateResponse(
        request,
        "download-requested-data.html",
        {
            "has_data": True,
            "row_count": len(rows),
            "size_bytes": len(csv_bytes),
            "default_filename": f"nyctograph_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        },
    )


@router.post("/research/download")
def research_download_action(
    request: Request,
    dbSes: DbSesDep,
    res: ResearcherDep,
    filename: str = Form(min_length=1),
):
    if not res:
        flash(request, "This page requires a research institution account.", "warn")
        return RedirectResponse("/login", status_code=303)

    if not res.data_filters:
        flash(request, "No requested data. Set filters first.", "warn")
        return RedirectResponse("/research/download", status_code=303)

    rows = res.fetch_matching_research_entries(dbSes, newest_first=False, limit=None)
    if not rows:
        flash(request, "No public entries match your current filters.", "warn")
        return RedirectResponse("/research/download", status_code=303)

    safe_name = (filename or "").strip() or "nyctograph_entries.csv"
    if not safe_name.lower().endswith(".csv"):
        safe_name += ".csv"

    csv_bytes = _generate_csv_bytes(rows)

    dbSes.add(
        DownloadRecord(
            researcher_id=res.id,
            downloaded_at=datetime.now(),
            filters_used=res.data_filters or "{}",
        )
    )
    dbSes.commit()

    # StreamingResponse matches team guidance + FastAPI CSV patterns (no temp file on disk).
    headers = {"Content-Disposition": f'attachment; filename="{safe_name}"'}
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )

def _generate_csv_bytes(rows: list[ResearchEntry]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(
        [
            "title",
            "description",
            "content_tags",
            "type_tags",
            "sense_sight",
            "sense_sound",
            "sense_touch",
            "sense_smell",
            "sense_taste",
            "sense_pain",
            "sense_other",
            "created_at",
            "context",
            "context_tags",
            "bed_time",
            "wake_time",
            "country",
            "state",
            "city",
            "reflection",
            "rfln_timestamp",
            "username",
            "user_gender",
            "user_age",
            "user_med_conditions",
        ]
    )

    for r in rows:
        writer.writerow(
            [
                r.title,
                r.description,
                r.content_tags,
                r.type_tags,
                r.sense_sight,
                r.sense_sound,
                r.sense_touch,
                r.sense_smell,
                r.sense_taste,
                r.sense_pain,
                r.sense_other,
                r.created_at.isoformat(sep=" ", timespec="seconds") if r.created_at else None,
                r.context,
                r.context_tags,
                r.bed_time.isoformat() if r.bed_time else None,
                r.wake_time.isoformat() if r.wake_time else None,
                r.country,
                r.state,
                r.city,
                r.reflection,
                r.rfln_timestamp.isoformat(sep=" ", timespec="seconds") if r.rfln_timestamp else None,
                r.username,
                r.user_gender,
                r.user_age,
                r.user_med_conditions,
            ]
        )

    return buf.getvalue().encode("utf-8")