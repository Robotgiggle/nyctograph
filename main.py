from argon2 import PasswordHasher
from typing import Annotated
from fastapi import FastAPI, Request, Form, Cookie, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

# ===== APP SETUP =====

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="correcthorsebatterystaple")

def flash_context(request: Request): return {"flash": request.session.pop("flashMessages", [])}
templates = Jinja2Templates(directory="templates", context_processors=[flash_context])

ph = PasswordHasher()

fake_db_users = {
    "admin": {
        "username": "admin",
        "pwhash": ph.hash("dream"),
        "number": 1868
    },
    "user1": {
        "username": "user1",
        "pwhash": ph.hash("pw123"),
        "number": 57
    }
}

# ===== UTILITIES =====

def validate_user(uname: str, pword: str):
    for user in fake_db_users.values():
        if user["username"] == uname and ph.verify(user["pwhash"], pword):
            return True
    return False

def get_user(request: Request):
    uname = request.session.get("uname")
    if uname: return fake_db_users.get(uname)
    else: return None

def flash(request: Request, message: str, type: str):
    if "flashMessages" not in request.session:
        request.session["flashMessages"] = []
    request.session["flashMessages"].append((message, type))

# ===== ROUTES =====

@app.get("/")
def root(request: Request):
    user = get_user(request)
    return templates.TemplateResponse(request, "root.html", {"user": user})

@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.post("/login")
def login_action(request: Request, uname: Annotated[str, Form()], pword: Annotated[str, Form()]):    
    if validate_user(uname, pword):
        request.session["uname"] = uname
        response = RedirectResponse("/", status_code=303)
    else:
        response = RedirectResponse("/login", status_code=303)
        flash(request, "Invalid credentials!", "warn")
    return response

@app.get("/logout")
def logout_action(request: Request):
    response = RedirectResponse("/", status_code=303)
    request.session.pop("uname", None)
    return response