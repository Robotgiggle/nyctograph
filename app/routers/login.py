from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..models import User
from ..utils import *
from ..jinja import templates

router = APIRouter()

# Page with login form
@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

# Login handler method
@router.post("/login")
def login_action(request: Request, dbSes: DbSesDep, uname: Annotated[str, Form()], pword: Annotated[str, Form()]):    
    result = dbSes.execute(select(User.id, User.pw_hash).where(User.username == uname)).first()
    
    if result and ph.verify(result[1], pword):
        request.session["user_id"] = result[0]
        request.session["username"] = uname
        response = RedirectResponse("/", status_code=303)
    else:
        response = RedirectResponse("/login", status_code=303)
        flash(request, "Invalid credentials!", "warn")

    return response