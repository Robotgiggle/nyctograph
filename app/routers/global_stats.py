from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func

from ..utils import DbSesDep, single_value_query, not_implemented_yet
from ..jinja import templates
from ..models import GlobalStats, TagAssociation

router = APIRouter()

# Page to display global stats
@router.get("/global-stats")
def view_global_stats(request: Request, dbSes: DbSesDep):
    stats_all: GlobalStats|None = single_value_query(dbSes, select(GlobalStats).where(GlobalStats.time_slice == "all", GlobalStats.age_bracket == "all"), None)
    
    if stats_all is not None:
        associations = map(lambda row: row[0], dbSes.execute(
            select(TagAssociation)
            .where(TagAssociation.stats_obj == stats_all)
            .order_by(TagAssociation.association_strength.desc())
        ).all())
    else:
        associations = None

    return templates.TemplateResponse(request, "global-stats.html", {"stats": stats_all, "associations": associations})