from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..utils import not_implemented_yet
from ..jinja import templates

router = APIRouter()

# Page to display global stats
@router.get("/global-stats")
def view_global_stats(request: Request):
    return not_implemented_yet(request)