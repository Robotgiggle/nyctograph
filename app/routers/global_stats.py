from fastapi import APIRouter, Request
from sqlalchemy import select, func

from ..utils import DbSesDep
from ..jinja import templates
from ..models import GlobalStats, TagTotal, TagAssociation

router = APIRouter()

# Page to display global stats [REQ-4]
@router.get("/global-stats")
def view_global_stats(request: Request, dbSes: DbSesDep, time_slice: str = "all", age_bracket: str = "all"):
    statsQuery = select(GlobalStats).where(GlobalStats.time_slice == time_slice, GlobalStats.age_bracket == age_bracket)
    statsAll: GlobalStats|None = dbSes.scalar(statsQuery)
    tagTotals = {}
    tagCount = None
    associations = None

    if statsAll is not None:
        for cat in ["dream_content", "dream_type", "irl_context"]:
            tagTotals[cat] = dbSes.execute(
                select(TagTotal.tag_val, TagTotal.total)
                .where(TagTotal.stats_obj == statsAll, TagTotal.tag_cat == cat)
                .order_by(TagTotal.total.desc())
            ).all()
        tagCount = dbSes.scalar(
            select(func.sum(TagTotal.total))
            .where(TagTotal.stats_obj == statsAll)
        )
        associations = dbSes.scalars(
            select(TagAssociation)
            .where(TagAssociation.stats_obj == statsAll)
            .order_by(TagAssociation.association_strength.desc())
        ).all()
        
    context = {
        "stats": statsAll, 
        "totals": tagTotals, 
        "tagCount": tagCount,
        "associations": associations,
        "time_slice": time_slice,
        "age_bracket": age_bracket
    }

    return templates.TemplateResponse(request, "global-stats.html", context)