from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..utils import *
from ..jinja import templates

router = APIRouter()

# Page listing stored dream entries and local stats
@router.get("/my-dreams")
def list_dream_entries(request: Request, dbSes: DbSesDep, user: UserDep):
    if not user:
        flash(request, "This page or method requires an account!", "warn")
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "my-dreams.html", {"entries": user.dream_entries})

# Page to display the full details of a specific dream entry
@router.get("/my-dreams/{entry_id}")
def dream_entry_detail(request: Request, entry_id: int):
    return not_implemented_yet(request)