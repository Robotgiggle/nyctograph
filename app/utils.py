from argon2 import PasswordHasher
from fastapi import Request
from fastapi.responses import RedirectResponse

# Object used throughout the app for hashing
ph = PasswordHasher()

# Minimal database representation until we set up the real one
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

# Returns a data structure representing the logged-in user
# Returns None if not logged in
def get_user(request: Request):
    uname = request.session.get("uname")
    if uname: return fake_db_users.get(uname)
    else: return None

# Adds a message to the flash list, to be displayed the next time a page is loaded
def flash(request: Request, message: str, type: str):
    if "flashMessages" not in request.session:
        request.session["flashMessages"] = []
    request.session["flashMessages"].append((message, type))

# Returns True if the specified account exists, and False otherwise
def validate_user(uname: str, pword: str):
    for user in fake_db_users.values():
        if user["username"] == uname and ph.verify(user["pwhash"], pword):
            return True
    return False

# Return this from a path operation if the actual functionality hasn't been implemented yet
def not_implemented_yet(request: Request):
    flash(request, "This page or method ("+str(request.url)+") has not been implemented yet!", "warn")
    return RedirectResponse("/", status_code=303)