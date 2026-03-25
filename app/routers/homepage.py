from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from ..models import DreamEntry, Tag
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
        new_entry = DreamEntry(
            title=title, 
            description=description, 
            created_at=datetime.now(), 
            public=False
        )
        user.dream_entries.append(new_entry)
        dbSes.add(user)
        dbSes.commit()
        flash(request, "Dream entry saved", "info")
        return RedirectResponse("/", status_code=303)
    else:
        # TODO: use something other than a tuple here (probably a dict? maybe a whole DreamEntry?)
        request.session["storedEntry"] = (title, description)
        flash(request, "Dream entry temporarily stored - create an account to save it!", "info")
        return RedirectResponse("/signup", status_code=303)