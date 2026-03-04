from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from ..models import DreamEntry
from ..utils import *
from ..jinja import templates

router = APIRouter()

@router.get("/")
def record_dream_form(request: Request):
    storedEntry = request.session.get("storedEntry")
    return templates.TemplateResponse(request, "record-dream.html", {"entry": storedEntry})

@router.post("/")
def record_dream_action(request: Request, dbSes: DbSesDep, user: UserDep, title: Annotated[str, Form()], description: Annotated[str, Form()]):
    if user:
        user.dream_entries.append(DreamEntry(title=title, description=description, public=False))
        dbSes.add(user)
        dbSes.commit()
        flash(request, "Dream entry saved", "info")
        return RedirectResponse("/", status_code=303)
    else:
        request.session["storedEntry"] = (title, description)
        flash(request, "Dream entry temporarily stored - create an account to save it!", "info")
        return RedirectResponse("/signup", status_code=303)