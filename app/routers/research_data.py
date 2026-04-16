import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, StreamingResponse

from ..jinja import templates
from ..models import DownloadRecord, ResearchEntry, Researcher
from ..models.researcher import parse_iso_date
from ..utils import DbSesDep, ResearcherDep, flash

router = APIRouter()


def _require_researcher(request: Request, researcher: ResearcherDep) -> Researcher | RedirectResponse:
    if not researcher:
        flash(request, "This page requires a research institution account.", "warn")
        return RedirectResponse("/login", status_code=303)
    return researcher


@router.get("/request-data")
def request_data_page(request: Request, dbSes: DbSesDep, researcher: ResearcherDep):
    res = _require_researcher(request, researcher)
    if isinstance(res, RedirectResponse):
        return res

    filters = res.parsed_filters()
    return templates.TemplateResponse(request, "request-data.html", {"filters": filters})


@router.post("/request-data")
def request_data_action(
    request: Request,
    dbSes: DbSesDep,
    researcher: ResearcherDep,
    start_date: str | None = Form(default=None),
    end_date: str | None = Form(default=None),
    country: str | None = Form(default=None),
    state: str | None = Form(default=None),
    city: str | None = Form(default=None),
):
    res = _require_researcher(request, researcher)
    if isinstance(res, RedirectResponse):
        return res

    try:
        parse_iso_date(start_date)
        parse_iso_date(end_date)
    except Exception:
        flash(request, "Invalid date format. Use YYYY-MM-DD.", "warn")
        return RedirectResponse("/request-data", status_code=303)

    filters = {
        "start_date": (start_date or "").strip() or None,
        "end_date": (end_date or "").strip() or None,
        "country": (country or "").strip() or None,
        "state": (state or "").strip() or None,
        "city": (city or "").strip() or None,
    }
    res.data_filters = json.dumps(filters)
    dbSes.commit()

    flash(request, "Filters saved. You can now view and download matching public entries.", "success")
    return RedirectResponse("/view-requested-data", status_code=303)


@router.get("/view-requested-data")
def view_requested_data_page(request: Request, dbSes: DbSesDep, researcher: ResearcherDep):
    res = _require_researcher(request, researcher)
    if isinstance(res, RedirectResponse):
        return res

    if not res.data_filters:
        flash(request, "No requested data. Set filters first.", "warn")
        return templates.TemplateResponse(request, "view-requested-data.html", {"entries": [], "filters": {}})

    filters = res.parsed_filters()
    entries = res.fetch_matching_research_entries(dbSes, newest_first=True, limit=200)

    return templates.TemplateResponse(
        request,
        "view-requested-data.html",
        {"entries": entries, "filters": filters, "limited": True},
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


@router.get("/download-requested-data")
def download_requested_data_page(request: Request, dbSes: DbSesDep, researcher: ResearcherDep):
    res = _require_researcher(request, researcher)
    if isinstance(res, RedirectResponse):
        return res

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


@router.post("/download-requested-data")
def download_requested_data_action(
    request: Request,
    dbSes: DbSesDep,
    researcher: ResearcherDep,
    filename: str = Form(min_length=1),
):
    res = _require_researcher(request, researcher)
    if isinstance(res, RedirectResponse):
        return res

    if not res.data_filters:
        flash(request, "No requested data. Set filters first.", "warn")
        return RedirectResponse("/download-requested-data", status_code=303)

    rows = res.fetch_matching_research_entries(dbSes, newest_first=False, limit=None)
    if not rows:
        flash(request, "No public entries match your current filters.", "warn")
        return RedirectResponse("/download-requested-data", status_code=303)

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
