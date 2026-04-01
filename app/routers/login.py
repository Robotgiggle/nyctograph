from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..models import Researcher, User
from ..utils import *
from ..jinja import templates

router = APIRouter()

# Page with login form
@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

# Login handler method — standard users first, then research accounts (same username cannot exist in both)
@router.post("/login")
def login_action(request: Request, dbSes: DbSesDep, uname: Annotated[str, Form()], pword: Annotated[str, Form()]):
    user_row = dbSes.execute(select(User.id, User.pw_hash).where(User.username == uname)).first()
    if user_row and verify_pw(user_row[1], pword):
        request.session.pop("researcher_id", None)
        request.session["user_id"] = user_row[0]
        request.session["username"] = uname
        return RedirectResponse("/", status_code=303)

    res_row = dbSes.execute(select(Researcher.id, Researcher.pw_hash).where(Researcher.username == uname)).first()
    if res_row and verify_pw(res_row[1], pword):
        request.session.pop("user_id", None)
        request.session["researcher_id"] = res_row[0]
        request.session["username"] = uname
        return RedirectResponse("/", status_code=303)

    flash(request, "Invalid credentials!", "warn")
    return RedirectResponse("/login", status_code=303)