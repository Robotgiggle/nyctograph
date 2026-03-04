from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..utils import not_implemented_yet
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
def account_config_page(request: Request):
    return not_implemented_yet(request)

# Account config handler method
@router.post("/account")
def account_config_action(request: Request):
    return not_implemented_yet(request)