from typing import Annotated

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..forms import ResearchSignupRequestForm, StandardSignupForm
from ..models import User, Researcher, ResearchRequest
from ..utils import DbSesDep, flash, ph
from ..jinja import templates

router = APIRouter()


def _username_taken(dbSes, username: str) -> bool:
    u = dbSes.execute(select(User.id).where(User.username == username)).first()
    r = dbSes.execute(select(Researcher.id).where(Researcher.username == username)).first()
    return u is not None or r is not None


def _email_taken(dbSes, email: str) -> bool:
    u = dbSes.execute(select(User.id).where(User.email == email)).first()
    r = dbSes.execute(select(Researcher.id).where(Researcher.email == email)).first()
    return u is not None or r is not None


@router.get("/signup")
def signup_form(request: Request):
    return templates.TemplateResponse(request, "signup.html", {})


@router.post("/signup")
def signup_action(request: Request, dbSes: DbSesDep, form: Annotated[StandardSignupForm, Form()]):
    if _username_taken(dbSes, form.username):
        flash(request, "That username is already taken.", "warn")
        return RedirectResponse("/signup", status_code=303)
    if _email_taken(dbSes, str(form.email)):
        flash(request, "That email is already registered.", "warn")
        return RedirectResponse("/signup", status_code=303)

    user = User(
        username=form.username,
        pw_hash=ph.hash(form.password),
        email=str(form.email),
        public_enabled=form.public_enabled
    )
    dbSes.add(user)
    dbSes.commit()
    dbSes.refresh(user)

    request.session.pop("researcher_id", None)
    request.session["user_id"] = user.id
    request.session["username"] = user.username

    flash(request, "Account created. You are now logged in.", "success")
    return RedirectResponse("/", status_code=303)


@router.get("/signup/research")
def research_signup_form(request: Request):
    return templates.TemplateResponse(request, "research-signup-request.html", {})


@router.post("/signup/research")
def research_signup_action(
    request: Request,
    dbSes: DbSesDep,
    form: Annotated[ResearchSignupRequestForm, Form()],
):
    if _email_taken(dbSes, str(form.email)):
        flash(request, "That email is already used by an existing account.", "warn")
        return RedirectResponse("/signup/research", status_code=303)

    newReq = ResearchRequest(
        name=form.name,
        email=str(form.email),
        ror_id=form.ror_id,
        reason=form.reason
    )
    dbSes.add(newReq)
    dbSes.commit()

    flash(request, "Account request submitted! We will get back to you shortly.", "success")
    return RedirectResponse("/signup/research", status_code=303)

# @router.post("/signup/research")
# def research_signup_action(
#     request: Request,
#     dbSes: DbSesDep,
#     form: Annotated[ResearchSignupForm, Form()],
# ):
#     if _username_taken(dbSes, form.username):
#         flash(request, "That username is already taken.", "warn")
#         return RedirectResponse("/signup/research", status_code=303)
#     if _email_taken(dbSes, str(form.email)):
#         flash(request, "That email is already registered.", "warn")
#         return RedirectResponse("/signup/research", status_code=303)

#     researcher = Researcher(
#         username=form.username,
#         pw_hash=ph.hash(form.password),
#         email=str(form.email),
#         ror_id=form.ror_id
#     )
#     dbSes.add(researcher)
#     dbSes.commit()
#     dbSes.refresh(researcher)

#     request.session.pop("user_id", None)
#     request.session["researcher_id"] = researcher.id
#     request.session["username"] = researcher.username

#     flash(request, "Research account created. You are now logged in.", "success")
#     return RedirectResponse("/research", status_code=303)
