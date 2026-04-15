from os.path import dirname
from fastapi import Request
from fastapi.templating import Jinja2Templates
from typing import Any

# Setup for Jinja2 template engine

def global_context(request: Request):
    return {
        "flash": request.session.pop("flashMessages", []),
        "uname": request.session.get("username"),
        "login_status": 2 if request.session.get("researcher_id") else (1 if request.session.get("user_id") else 0)
    }

templates = Jinja2Templates(directory=dirname(__file__)+"/templates", context_processors=[global_context])

def template_string(name: str, context: dict[str, Any] | None = None):
    temp = templates.env.get_template(name)
    if context: return temp.render(**context)
    else: return temp.render()