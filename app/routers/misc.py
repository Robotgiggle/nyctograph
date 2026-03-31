from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from ..utils import UserDep, DbSesDep, flash, verify_pw, ph, not_implemented_yet
from ..jinja import templates

router = APIRouter()

# Page explaining what Nyctograph is
@router.get("/about-us")
def about_us(request: Request):
    return not_implemented_yet(request)

# Route that logs you out when visited
@router.get("/logout")
def logout_action(request: Request):
    response = RedirectResponse("/", status_code=303)
    request.session.pop("user_id", None)
    request.session.pop("username", None)
    return response

# Page for configuring account settings
@router.get("/account")
def account_config_page(request: Request, user: UserDep):
    if not user:
        flash(request, "You must be logged in to access account settings.", "warn")
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "account.html", {"user": user})

# Account config handler method
@router.post("/account")
def account_config_action(
    request: Request,
    user: UserDep,
    dbSes: DbSesDep,
    email: Annotated[str | None, Form()] = None,
    new_username: Annotated[str | None, Form()] = None,
    current_password: Annotated[str | None, Form()] = None,
    new_password: Annotated[str | None, Form()] = None,
    public_enabled: Annotated[bool | None, Form()] = None,
    age: Annotated[int | None, Form()] = None,
    gender: Annotated[str | None, Form()] = None,
    med_conditions: Annotated[str | None, Form()] = None,
    country: Annotated[str | None, Form()] = None,
    state: Annotated[str | None, Form()] = None,
    city: Annotated[str | None, Form()] = None,
):
    if not user:
        flash(request, "You must be logged in to update account settings.", "warn")
        return RedirectResponse("/login", status_code=303)

    # Handle password change. Requires current password to be verified first
    if new_password:
        if not current_password or not verify_pw(user.pw_hash, current_password):
            flash(request, "Current password is incorrect.", "warn")
            return RedirectResponse("/account", status_code=303)
        user.pw_hash = ph.hash(new_password)

    # Update each field if it was submitted; empty string clears optional text fields
    if email is not None:
        user.email = email
    if new_username is not None and new_username != "":
        user.username = new_username
        request.session["username"] = new_username
    if public_enabled is not None:
        user.public_enabled = public_enabled
    if age is not None:
        user.age = age
    if gender is not None:
        user.gender = gender or None
    if med_conditions is not None:
        user.med_conditions = med_conditions or None
    if country is not None:
        user.country = country or None
    if state is not None:
        user.state = state or None
    if city is not None:
        user.city = city or None

    dbSes.commit()
    flash(request, "Account settings updated.", "success")
    return RedirectResponse("/account", status_code=303)
