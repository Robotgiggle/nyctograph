from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from ..utils import flash, validate_user, not_implemented_yet
from ..jinja import templates

router = APIRouter()

# Page with sign-up form
@router.get("/signup")
def signup_form(request: Request):
    return not_implemented_yet(request)

# Sign-up handler method
@router.post("/signup")
def signup_action(request: Request): 
    return not_implemented_yet(request)

# Page with login form
@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

# Login handler method
@router.post("/login")
def login_action(request: Request, uname: Annotated[str, Form()], pword: Annotated[str, Form()]):    
    if validate_user(uname, pword):
        request.session["uname"] = uname
        response = RedirectResponse("/", status_code=303)
    else:
        response = RedirectResponse("/login", status_code=303)
        flash(request, "Invalid credentials!", "warn")
    return response

# Visiting this page logs you out
@router.get("/logout")
def logout_action(request: Request):
    response = RedirectResponse("/", status_code=303)
    request.session.pop("uname", None)
    return response