from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..models import DreamEntry
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
def dream_entry_detail(request: Request, entry_id: int, dbSes: DbSesDep, user: UserDep):
    # Get the dream entry from database
    entry = dbSes.get(DreamEntry, entry_id)
    
    # Handle entry not found
    if not entry:
        flash(request, "Dream entry not found!", "warn")
        return RedirectResponse("/my-dreams" if user else "/", status_code=303)
    
    # Check permissions: public entries can be viewed by anyone,
    # private entries can only be viewed by the owner
    if not entry.public and (not user or entry.user_id != user.id):
        flash(request, "You don't have permission to view this dream entry!", "warn")
        return RedirectResponse("/my-dreams" if user else "/login", status_code=303)
    
    # Render the detail page
    return templates.TemplateResponse(request, "dream-detail.html", {"entry": entry})