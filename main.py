from argon2 import PasswordHasher
from typing import Annotated
from fastapi import FastAPI, Request, Form, Cookie, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

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

def global_context(request: Request): 
    return {
        "flash": request.session.pop("flashMessages", []),
        "uname": request.session.get("uname")
    }

def not_implemented_yet(request: Request):
    flash(request, "This page or method ("+str(request.url)+") has not been implemented yet!", "warn")
    return RedirectResponse("/", status_code=303)

# ===== APP SETUP =====

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="correcthorsebatterystaple")

templates = Jinja2Templates(directory="templates", context_processors=[global_context])

ph = PasswordHasher()

fake_db_users = {
    "user1": {
        "username": "user1",
        "pwhash": ph.hash("pw123"),
        "entries": []
    },
    "user2": {
        "username": "user2",
        "pwhash": ph.hash("pw456"),
        "entries": []
    }
}

# ===== ROUTES =====

# homepage / dream entry form
@app.get("/")
def record_dream_form(request: Request):
    storedEntry = request.session.get("storedEntry")
    return templates.TemplateResponse(request, "record_dream.html", {"entry": storedEntry})

@app.post("/")
def record_dream_action(request: Request, title: Annotated[str, Form()], description: Annotated[str, Form()]):
    user = get_user(request)
    if user:
        user["entries"].append((title, description))
        flash(request, "Dream entry saved", "info")
        return RedirectResponse("/", status_code=303)
    else:
        request.session["storedEntry"] = (title, description)
        flash(request, "Dream entry temporarily stored - create an account to save it!", "info")
        return RedirectResponse("/signup", status_code=303)
    
# view stored entries

@app.get("/my-dreams")
def list_dream_entries(request: Request):
    user = get_user(request)
    if not user:
        flash(request, "This page or method requires an account!", "warn")
        return RedirectResponse("/login", status_code=303)
    entries = user["entries"]
    print(entries)
    return templates.TemplateResponse(request, "my-dreams.html", {"entries": entries})

# view global stats

@app.get("/global-stats")
def view_global_stats(request: Request):
    return not_implemented_yet(request)

# general info page

@app.get("/about-us")
def about_us(request: Request):
    return not_implemented_yet(request)

# account creation

@app.get("/signup")
def signup_form(request: Request):
    return not_implemented_yet(request)

@app.post("/signup")
def signup_action(request: Request): 
    return not_implemented_yet(request)

# login system

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