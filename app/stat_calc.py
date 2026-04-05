import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, delete, desc, func
from sqlalchemy.orm import Session
import logging

from .models import DreamEntry, User, Tag, TagAssociation, GlobalStats
from .database import engine

logger = logging.getLogger("uvicorn")

def tag_results_to_dict(tagResults):
    output = {
        "dream_content": (None, None),
        "dream_type": (None, None),
        "irl_context": (None, None)
    }
    for row in tagResults:
        output[row[0]] = (row[1], row[2])
    return output

def apply_age_bracket_filter(query, ageBracket):
    if ageBracket:
        return query.where(
            func.extract("day", (func.now() - User.birth_date)/365.25) > ageBracket[0],
            func.extract("day", (func.now() - User.birth_date)/365.25) < ageBracket[1]
        )
    else:
        return query

baseStatQuery = select(
    func.count(), 
    func.count().filter(DreamEntry.sense_sight == True), 
    func.count().filter(DreamEntry.sense_sound == True), 
    func.count().filter(DreamEntry.sense_touch == True), 
    func.count().filter(DreamEntry.sense_smell == True), 
    func.count().filter(DreamEntry.sense_taste == True), 
    func.count().filter(DreamEntry.sense_pain == True), 
    func.count().filter(DreamEntry.sense_other == True), 
    func.coalesce(func.avg(DreamEntry.sleep_hours), 0)
).join(User).where(DreamEntry.public == True)

baseTagQuery = (
    select(Tag.category, Tag.value, func.count().label("total"))    # Select all tags along with the
    .join(Tag, DreamEntry.tags).join(User)                          # number of times they appear
    .where(DreamEntry.public == True, Tag.category != 'calculated') #
    .group_by(Tag.value)                                            #
    .distinct(Tag.category)                # Only keep the tag in each category with the biggest total
    .order_by(Tag.category, desc('total')) # 
)

async def calculate_global_stats(interval_mins: float):
    while True:
        dbSes = Session(engine)

        # remove the data from the last calculation run
        dbSes.execute(delete(GlobalStats))

        # calculate new global stats
        for daysIncluded in [1, 7, 30, None]:
            cutoffDate = datetime.today() - timedelta(days=daysIncluded) if daysIncluded else datetime.min
            sqDayFiltered = baseStatQuery.where(DreamEntry.created_at > cutoffDate)
            tqDayFiltered = baseTagQuery.where(DreamEntry.created_at > cutoffDate)
            for ageBracket in [(13,29), (30,49), (50,999), None]:
                sqDayAgeFiltered = apply_age_bracket_filter(sqDayFiltered, ageBracket)
                tqDayAgeFiltered = apply_age_bracket_filter(tqDayFiltered, ageBracket)
                statResults = dbSes.execute(sqDayAgeFiltered).first()
                tagResults1 = dbSes.execute(tqDayAgeFiltered).all()
                t1Dict = tag_results_to_dict(tagResults1)
                topTags = map(lambda e: e[0], t1Dict.values())
                tagResults2 = dbSes.execute(tqDayAgeFiltered.where(Tag.value.not_in(topTags))).all()
                t2Dict = tag_results_to_dict(tagResults2)
                newStatsObj = GlobalStats(
                    time_slice = {1: "day", 7: "week", 30: "month", None: "all"}[daysIncluded],
                    age_bracket = {(13,29): "13-29", (30,49): "30-49", (50,999): "50+", None: "all"}[ageBracket],
                    total_entries = statResults[0] if statResults else 0,
                    top_content_tag = t1Dict["dream_content"][0],
                    top_content_tag_count = t1Dict["dream_content"][1],
                    second_content_tag = t2Dict["dream_content"][0],
                    second_content_tag_count = t2Dict["dream_content"][1],
                    top_context_tag = t1Dict["irl_context"][0],
                    top_context_tag_count = t1Dict["irl_context"][1],
                    second_context_tag = t2Dict["irl_context"][0],
                    second_context_tag_count = t2Dict["irl_context"][1],
                    top_type_tag = t1Dict["dream_type"][0],
                    top_type_tag_count = t1Dict["dream_type"][1],
                    second_type_tag = t2Dict["dream_type"][0],
                    second_type_tag_count = t2Dict["dream_type"][1],
                    sight_rate = statResults[1]/statResults[0] if statResults and statResults[0] else 0,
                    sound_rate = statResults[2]/statResults[0] if statResults and statResults[0] else 0,
                    touch_rate = statResults[3]/statResults[0] if statResults and statResults[0] else 0,
                    smell_rate = statResults[4]/statResults[0] if statResults and statResults[0] else 0,
                    taste_rate = statResults[5]/statResults[0] if statResults and statResults[0] else 0,
                    pain_rate = statResults[6]/statResults[0] if statResults and statResults[0] else 0,
                    other_rate = statResults[7]/statResults[0] if statResults and statResults[0] else 0,
                    avg_sleep_duration = statResults[8] if statResults else 0
                )
                dbSes.add(newStatsObj)
        # TODO: calculate tag associations
        dbSes.commit()
        dbSes.close()
        
        # this gets the full total since the none/none filter case is the last one in the loop
        logger.info("Global statistics calculated from %d public entries.", statResults[0] if statResults else 0)

        # attempt to recalculate every time the interval passes, but only if there are new entries
        recalculate = False
        while not recalculate:
            await asyncio.sleep(60 * interval_mins)
            latest = dbSes.execute(select(func.max(DreamEntry.created_at))).first()
            if latest and latest[0] >= datetime.now() - timedelta(minutes=interval_mins):
                recalculate = True