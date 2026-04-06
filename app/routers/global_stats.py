from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func

from ..utils import DbSesDep, single_value_query, not_implemented_yet
from ..jinja import templates
from ..models import GlobalStats, TagTotal, TagAssociation

router = APIRouter()

# Page to display global stats
@router.get("/global-stats")
def view_global_stats(request: Request, dbSes: DbSesDep):
    stats_all: GlobalStats|None = single_value_query(dbSes, select(GlobalStats).where(GlobalStats.time_slice == "all", GlobalStats.age_bracket == "all"), None)
    tag_totals = {}
    associations = None

    if stats_all is not None:
        for cat in ["dream_content", "dream_type", "irl_context"]:
            tag_totals[cat] = dbSes.execute(
                select(TagTotal.tag_val, TagTotal.total)
                .where(TagTotal.stats_obj == stats_all, TagTotal.tag_cat == cat)
                .order_by(TagTotal.total.desc())
            ).all()
        associations = map(lambda row: row[0], dbSes.execute(
            select(TagAssociation)
            .where(TagAssociation.stats_obj == stats_all)
            .order_by(TagAssociation.association_strength.desc())
        ).all())
        

    return templates.TemplateResponse(request, "global-stats.html", {"stats": stats_all, "totals": tag_totals, "associations": associations})