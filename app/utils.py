from argon2 import PasswordHasher
from typing import Annotated
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import engine
from .models import User

# Hasher object used throughout the app
ph = PasswordHasher()

# [DEPENDENCY] Creates a database session, then closes it once the path operation finishes
def get_db_ses():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
# Type alias for the dependency
DbSesDep = Annotated[Session, Depends(get_db_ses)]

# [DEPENDENCY] Provides the logged-in user, or None if not logged in
def get_user(request: Request, dbSes: DbSesDep):
    id = request.session.get("user_id")
    if id: return dbSes.get(User, id)
    else: return None
# Type alias for the dependency
UserDep = Annotated[User, Depends(get_user)]

# Adds a message to the flash list, to be displayed the next time a page is loaded
def flash(request: Request, message: str, type: str):
    if "flashMessages" not in request.session:
        request.session["flashMessages"] = []
    request.session["flashMessages"].append((message, type))

# Return this from a path operation if the actual functionality hasn't been implemented yet
def not_implemented_yet(request: Request):
    flash(request, "This page or method ("+str(request.url)+") has not been implemented yet!", "warn")
    return RedirectResponse("/", status_code=303)