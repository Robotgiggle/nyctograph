from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from ..utils import get_user, flash
from ..jinja import templates

router = APIRouter()

@router.get("/")
def record_dream_form(request: Request):
    storedEntry = request.session.get("storedEntry")
    return templates.TemplateResponse(request, "record_dream.html", {"entry": storedEntry})

@router.post("/")
def record_dream_action(request: Request, title: Annotated[str, Form()], description: Annotated[str, Form()]):
    user = get_user(request)
    if user:
        user["entries"].append((title, description))
        flash(request, "Dream entry saved", "info")
        return RedirectResponse("/", status_code=303)
    else:
        request.session["storedEntry"] = (title, description)
        flash(request, "Dream entry temporarily stored - create an account to save it!", "info")
        return RedirectResponse("/signup", status_code=303)