from typing import Annotated
from fastapi import BackgroundTasks, APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from os import urandom

from ..utils import UserDep, DbSesDep, flash, verify_pw, ph, not_implemented_yet
from ..jinja import templates
from ..forms import AccountConfigForm
from ..models import User, ResearchRequest, DreamEntry
from ..email import send_research_approval, send_research_denial

router = APIRouter()

# Admin control page
@router.get("/admin")
def admin_page(request: Request, user: UserDep, dbSes: DbSesDep):
    if not user or user.username != "admin":
        flash(request, "You do not have permission to access this page!", "warn")
        return RedirectResponse("/", status_code=303)
    
    requests = dbSes.scalars(select(ResearchRequest)).all()

    return templates.TemplateResponse(request, "admin.html", {"requests": requests})

# Admin page action (approving/denying research account requests)
@router.post("/admin")
def admin_action(
    request: Request, 
    bg_tasks: BackgroundTasks,
    user: UserDep, 
    dbSes: DbSesDep, 
    req_id: Annotated[int, Form()], 
    approval: Annotated[str, Form()],
    deny_msg: Annotated[str, Form()] = ""
):
    if not user or user.username != "admin":
        flash(request, "You do not have permission for this action!", "warn")
        return RedirectResponse("/", status_code=303)
    
    req = dbSes.get(ResearchRequest, req_id)
    if req is None:
        flash(request, f"Research request with ID {req_id} not found in DB!", "warn")
        return RedirectResponse("/admin", status_code=303)

    if approval == "Approve":
        req.status = "Approved"
        req.token = ph.hash(urandom(20))[31:]
        bg_tasks.add_task(send_research_approval, req.email, req.name, req.token or "")
        flash(request, "Research request approved.", "success")
    elif approval == "Deny":
        dbSes.delete(req)
        bg_tasks.add_task(send_research_denial, req.email, req.name, req.reason, deny_msg)
        flash(request, "Research request denied.", "success")
    dbSes.commit()

    return RedirectResponse("/admin", status_code=303)

# Page explaining what Nyctograph is
@router.get("/about-us")
def about_us(request: Request):
    return templates.TemplateResponse(request, "about-us.html", {})

# Route that logs you out when visited
@router.get("/logout")
def logout_action(request: Request):
    response = RedirectResponse("/", status_code=303)
    request.session.pop("user_id", None)
    request.session.pop("researcher_id", None)
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
def account_config_action(request: Request, user: UserDep, dbSes: DbSesDep, formData: Annotated[AccountConfigForm, Form()]):
    if not user:
        flash(request, "You must be logged in to update account settings.", "warn")
        return RedirectResponse("/login", status_code=303)

    # Handle password change. Requires current password to be verified first
    if formData.new_password:
        if not formData.current_password or not verify_pw(user.pw_hash, formData.current_password):
            flash(request, "Current password is incorrect.", "warn")
            return RedirectResponse("/account", status_code=303)
        user.pw_hash = ph.hash(formData.new_password)

    # Update each field if it was submitted; empty string clears optional text fields
    if formData.email is not None:
        user.email = formData.email
    if formData.new_username is not None:
        existing = dbSes.execute(select(User.id).where(User.username == formData.new_username)).first()
        if existing and user.id != existing[0]:
            flash(request, "That username is already in use.", "warn")
            return RedirectResponse("/account", status_code=303)
        user.username = formData.new_username
        request.session["username"] = formData.new_username
    if formData.public_enabled is not None:
        # If changing from public to private, make all existing entries private
        if user.public_enabled and not formData.public_enabled:
            # Get all public dream entries for this user and make them private
            public_entries = dbSes.scalars(
                select(DreamEntry).where(
                    DreamEntry.user_id == user.id,
                    DreamEntry.public == True
                )
            ).all()
            
            for entry in public_entries:
                entry.public = False
            
            if len(public_entries) > 0:
                flash(request, f"{len(public_entries)} public dream entries have been made private.", "info")
        
        user.public_enabled = formData.public_enabled
    if formData.notif_enabled is not None:
        user.notif_enabled = formData.notif_enabled
    if formData.birth_date is not None:
        user.birth_date = formData.birth_date or None
    if formData.gender is not None:
        user.gender = formData.gender or None
    if formData.med_conditions is not None:
        user.med_conditions = formData.med_conditions or None
    if formData.country is not None:
        user.country = formData.country or None
    if formData.state is not None:
        user.state = formData.state or None
    if formData.city is not None:
        user.city = formData.city or None

    dbSes.commit()
    flash(request, "Account settings updated.", "success")
    return RedirectResponse("/account", status_code=303)
