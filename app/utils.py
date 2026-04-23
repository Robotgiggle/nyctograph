from argon2 import PasswordHasher
from typing import Annotated, Any
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import Select
from sqlalchemy.orm import Session

from .database import engine
from .models import User, Researcher

ph = PasswordHasher()

# ====== PATH OPERATION DEPENDENCIES ======

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
UserDep = Annotated[User | None, Depends(get_user)]

# [DEPENDENCY] Logged-in researcher, or None
def get_researcher(request: Request, dbSes: DbSesDep):
    rid = request.session.get("researcher_id")
    if rid is None:
        return None
    return dbSes.get(Researcher, rid)
# Type alias for the dependency
ResearcherDep = Annotated[Researcher | None, Depends(get_researcher)]

# ====== GENERAL UTILITY FUNCTIONS ======

def verify_pw(hashed_pw: str, input_pw: str):
    """Returns T/F based on whether the hashed password matches the provided string"""
    
    try:
        ph.verify(hashed_pw, input_pw)
        return True
    except:
        return False

def inv_lerp(start: float, end: float, value: float):
    """Inverse linear interpolation (how far from `start` to `end` is `value`?)"""

    return (value - start) / (end - start)

def flash(request: Request, message: str, type: str):
    """Adds a message to the flash list, to be displayed the next time a page is loaded"""

    if "flashMessages" not in request.session:
        request.session["flashMessages"] = []
    request.session["flashMessages"].append((message, type))

def not_implemented_yet(request: Request, redirect: str = "/"):
    """Return this from a path operation if the actual functionality hasn't been implemented yet"""

    flash(request, "This page or method ("+str(request.url)+") has not been implemented yet!", "warn")
    return RedirectResponse(redirect, status_code=303)

def page_range(page: int, total_pages: int) -> list[int]:
    """Return page numbers to display, using -1 as an ellipsis marker."""

    if total_pages <= 7:
        return list(range(1, total_pages + 1))
    pages: list[int] = [1]
    if page > 3:
        pages.append(-1)
    for p in range(max(2, page - 1), min(total_pages, page + 2)):
        pages.append(p)
    if page < total_pages - 2:
        pages.append(-1)
    if total_pages not in pages:
        pages.append(total_pages)
    return pages

def sizeof_fmt(num, suffix="B"):
    """Convert a number of bytes to a human-readable file size"""
    
    if num < 1000.0: return f"{num:d} bytes"
    for unit in ("K", "M", "G", "T", "P", "E", "Z"):
        num /= 1000.0
        if num < 1000.0:
            return f"{num:3.1f} {unit}{suffix}"
    return f"{num:.1f} Y{suffix}"
