from fastapi import Request
from fastapi.templating import Jinja2Templates

# Setup for Jinja2 template engine

def global_context(request: Request): 
    return {
        "flash": request.session.pop("flashMessages", []),
        "uname": request.session.get("username")
    }

templates = Jinja2Templates(directory="templates", context_processors=[global_context])