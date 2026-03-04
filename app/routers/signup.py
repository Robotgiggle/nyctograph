from typing import Annotated
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..models import User
from ..utils import *
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