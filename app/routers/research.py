import math
import csv
import io
import json
from typing import Annotated, Sequence
from fastapi import BackgroundTasks, APIRouter, Request, HTTPException, Body, Form
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import select, func
from datetime import datetime, date

from ..models import Tag, ResearchEntry, DataAccessRecord, User, Researcher
from ..forms import ResearchFilterForm
from ..utils import ResearcherDep, DbSesDep, flash
from ..jinja import templates
from ..email import send_data_access_notifs
from ..payment import create_checkout_session, get_checkout_session, mark_fulfilled

router = APIRouter()

@router.get("/research")
def research_filter_page(request: Request, res: ResearcherDep, dbSes: DbSesDep):
    if not res:
        flash(request, "This page requires a research account.", "warn")
        return RedirectResponse("/login", status_code=303)

    current_filters = ResearchFilterForm.from_json(res.pending_filters)

    all_tags = dbSes.scalars(select(Tag)).all()
    content_tags = [t.value for t in all_tags if t.category == "dream_content"]
    type_tags = [t.value for t in all_tags if t.category == "dream_type"]
    context_tags = [t.value for t in all_tags if t.category == "irl_context"]

    if res.pending_filters:
        countQuery = select(func.count()).select_from(ResearchEntry)
        matchQuery = res.filter_query(countQuery, pending=True)
        total_count = dbSes.scalar(countQuery)
        match_count = dbSes.scalar(matchQuery)
    else:
        total_count = match_count = None

    return templates.TemplateResponse(request, "research.html", {
        "filters": current_filters,
        "content_tags": content_tags,
        "type_tags": type_tags,
        "context_tags": context_tags,
        "match_count": match_count,
        "total_count": total_count,
        "today": date.today()
    })


@router.post("/research")
def research_filter_action(
    request: Request,
    res: ResearcherDep,
    dbSes: DbSesDep,
    formData: Annotated[ResearchFilterForm, Form()],
):
    if not res:
        flash(request, "This action requires a research account.", "warn")
        return RedirectResponse("/login", status_code=303)

    res.pending_filters = formData.to_json()
    dbSes.commit()
    flash(request, "Filters saved.", "success")
    return RedirectResponse("/research", status_code=303)


@router.post("/research/request")
def research_request_data_action(
    request: Request, 
    res: ResearcherDep,
    row_count: Annotated[int, Form()]
):
    if not res:
        flash(request, "This action requires a research account.", "warn")
        return RedirectResponse("/login", status_code=303)
    
    if not res.pending_filters:
        flash(request, "Please configure your filters before making a data request.", "warn")
        return RedirectResponse("/research", status_code=303)
    
    # create a checkout session with Stripe and redirect the user for payment
    checkoutSes = create_checkout_session(res, row_count, f"/research/request_success?rows={row_count}")
    checkoutURL = checkoutSes.url
    if checkoutURL is None:
        flash(request, "Checkout session creation failed.", "warn")
        return RedirectResponse("/research", status_code=303)
    return RedirectResponse(checkoutURL, status_code=303)


@router.get("/research/request_success")
def research_request_data_success(request: Request, rows: int):
    return templates.TemplateResponse(request, "research-request-success.html", {"rows": rows})


@router.post("/research/fulfill_request")
def research_request_data_fulfillment(payload: Annotated[dict, Body()], bgTasks: BackgroundTasks, dbSes: DbSesDep):
    # get the checkout session from Stripe
    checkoutSes = get_checkout_session(payload)
    checkoutData = checkoutSes.metadata

    # make sure the payment and request data are valid
    if checkoutData is None:
        raise HTTPException(status_code=400, detail="Checkout metadata is missing.")
    if checkoutData["fulfilled"] == "true":
        raise HTTPException(status_code=400, detail="This request has already been fulfilled.")
    if checkoutSes.payment_status == "unpaid":
        raise HTTPException(status_code=400, detail="This request has not yet been paid for.")
    res = dbSes.get(Researcher, checkoutData["res_id"])
    if res is None:
        raise HTTPException(status_code=400, detail="The researcher associated with this request cannot be found.")

    # mark the checkout session as fulfilled to avoid double fulfillment
    mark_fulfilled(checkoutSes)

    # lock in the filter settings
    res.data_filters = checkoutData["filters"]

    # store a record of the data access for transparency purposes
    dbSes.add(DataAccessRecord(
        researcher_id=res.id,
        accessed_at=datetime.now(),
        filters_used=res.data_filters,
    ))
    dbSes.commit()

    # send email notif to all matching users
    notifQuery = res.filter_query(
        select(User.email, User.username).distinct()
        .where(User.notif_enabled)
        .where(User.username == ResearchEntry.username)
    )
    userRows = dbSes.execute(notifQuery).all()
    bgTasks.add_task(send_data_access_notifs, userRows, res.ror_id, res.inst_name, checkoutData["rows"])

    return {"status": "success", "message": "Request successfully fulfilled!"}


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
        flash(request, "You have not yet requested access to any data!", "warn")
        return RedirectResponse("/research", status_code=303)

    if per_page not in (10, 25, 50):
        per_page = 10

    count_query = res.filter_query(select(func.count()).select_from(ResearchEntry))
    total_count = dbSes.scalar(count_query) or 0

    total_pages = max(1, math.ceil(total_count / per_page))
    page = max(1, min(page, total_pages))

    entries_query = res.filter_query(select(ResearchEntry).order_by(ResearchEntry.created_at.desc()))
    entries_query = entries_query.offset((page - 1) * per_page).limit(per_page)
    entries = dbSes.scalars(entries_query).all()

    return templates.TemplateResponse(request, "research-data.html", {
        "request_dt": res.get_last_access_dt(),
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
        flash(request, "You have not yet requested access to any data!", "warn")
        return RedirectResponse("/research", status_code=303)

    countQuery = res.filter_query(select(func.count()).select_from(ResearchEntry))
    sampleQuery = res.filter_query(select(ResearchEntry).order_by(func.random()).limit(10))
    count = dbSes.scalar(countQuery)
    sampleRows = dbSes.scalars(sampleQuery).all()
    if not count:
        flash(request, "No public entries match your current filters.", "warn")
        return templates.TemplateResponse(request, "research-download.html", {"has_data": False})

    estSizeBytes = estimate_download_size(sampleRows, count)

    return templates.TemplateResponse(
        request,
        "research-download.html",
        {
            "has_data": True,
            "row_count": count,
            "est_size": sizeof_fmt(estSizeBytes),
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
        flash(request, "You have not yet requested access to any data!", "warn")
        return RedirectResponse("/research", status_code=303)

    # retrieve all the data and convert it to CSV format
    dataQuery = res.filter_query(select(ResearchEntry).order_by(ResearchEntry.created_at.desc()))
    rows = dbSes.scalars(dataQuery).all()
    if not rows:
        flash(request, "No public entries match your current filters.", "warn")
        return RedirectResponse("/research/download", status_code=303)
    csv_iter = generate_csv_iter(rows)

    # define a filename
    safe_name = (filename or "").strip() or "nyctograph_entries.csv"
    if not safe_name.lower().endswith(".csv"):
        safe_name += ".csv"

    # send the CSV data to the client via a StreamingResponse
    headers = {"Content-Disposition": f'attachment; filename="{safe_name}"'}
    return StreamingResponse(
        csv_iter,
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


orderedColNames = [
    "title", "description", "content_tags", "type_tags", "sense_sight", "sense_sound", "sense_touch", 
    "sense_smell", "sense_taste", "sense_pain", "sense_other", "created_at", "context", "context_tags",
    "bed_time", "wake_time", "sleep_hours", "country", "state", "city", "not_at_home", "reflection", 
    "rfln_timestamp", "user_gender", "user_age", "user_med_conditions"
]


# Convert a number of bytes to a human-readable file size
def sizeof_fmt(num, suffix="B"):
    if num < 1000.0: return f"{num:d} bytes"
    for unit in ("K", "M", "G", "T", "P", "E", "Z"):
        num /= 1000.0
        if num < 1000.0:
            return f"{num:3.1f} {unit}{suffix}"
    return f"{num:.1f} Y{suffix}"


# Estimate the size of the file by averaging the size of a small sample of rows and multiplying by total row count
def estimate_download_size(sampleRows: Sequence[ResearchEntry], totalRows: int) -> int:
    # Write them to a test CSV
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=orderedColNames, extrasaction="ignore")
    writer.writerows(map(lambda entry: entry.__dict__, sampleRows))

    # Estimate size of full CSV (the extra 295 bytes is for the header)
    full = buf.getvalue()
    avgPerRow = len(full.encode("utf-8")) / len(sampleRows)
    return int(avgPerRow * totalRows) + 295


# Convert a list of ResearchEntry objects into a StringIO representing a CSV file.
# The output from this can be sent back to the client to make them download the file.
def generate_csv_iter(rows: Sequence[ResearchEntry]) -> io.StringIO:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=orderedColNames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(map(lambda entry: entry.__dict__, rows))

    buf.seek(0)
    
    return buf