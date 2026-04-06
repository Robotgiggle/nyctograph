import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, delete, desc, func
from sqlalchemy.orm import Session
import logging

from .models import DreamEntry, User, Tag, TagAssociation, GlobalStats
from .database import engine

logger = logging.getLogger("uvicorn")

def query_number(dbSes: Session, query):
    raw = dbSes.execute(query)
    return (raw.first() or [0])[0]

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

async def calculate_general_stats(dbSes: Session):
    # remove the data from the last calculation run
    dbSes.execute(delete(GlobalStats))

    # calculate new global stats, across four time periods and four age brackets
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

            # yield to the event loop to allow request handling mid-calculation
            await asyncio.sleep(0)

        # calculate completion percent
        completion = 25 * [1, 7, 30, None].index(daysIncluded)
        logger.info("[STATS] General statistics %.0f percent complete...", completion)

async def calculate_tag_associations(dbSes: Session):
    # remove the data from the last calculation run
    dbSes.execute(delete(TagAssociation))

    # calculate new tag associations
    tags = [*map(lambda row: row[0], dbSes.execute(select(Tag)).all())]
    for tagA in tags:
        for tagB in tags:
            # don't compare tags in the same category
            if tagA.category == tagB.category: continue

            # build the base forms of the two queries
            queryA = select(func.count()).join_from(DreamEntry, User).where(
                DreamEntry.public, 
                DreamEntry.tags.any(Tag.value == tagA.value)
            )
            queryAwithB = select(func.count()).join_from(DreamEntry, User).where(
                DreamEntry.public, 
                DreamEntry.tags.any(Tag.value == tagA.value), 
                DreamEntry.tags.any(Tag.value == tagB.value)
            )

            # loop across four time periods and four age brackets
            for daysIncluded in [1, 7, 30, None]:
                cutoffDate = datetime.today() - timedelta(days=daysIncluded) if daysIncluded else datetime.min
                qaDayFiltered = queryA.where(DreamEntry.created_at > cutoffDate)
                qabDayFiltered = queryAwithB.where(DreamEntry.created_at > cutoffDate)
                for ageBracket in [(13,29), (30,49), (50,999), None]:
                    qaDayAgeFiltered = apply_age_bracket_filter(qaDayFiltered, ageBracket)
                    qabDayAgeFiltered = apply_age_bracket_filter(qabDayFiltered, ageBracket)
                    totalA = query_number(dbSes, qaDayAgeFiltered)
                    if not totalA: continue
                    totalAwithB = query_number(dbSes, qabDayAgeFiltered)
                    newAssociation = TagAssociation(
                        tag_a = tagA,
                        tag_b = tagB,
                        time_slice = {1: "day", 7: "week", 30: "month", None: "all"}[daysIncluded],
                        age_bracket = {(13,29): "13-29", (30,49): "30-49", (50,999): "50+", None: "all"}[ageBracket],
                        association_rate = totalAwithB / totalA
                    )
                    dbSes.add(newAssociation)

                # yield to the event loop to allow request handling mid-calculation
                await asyncio.sleep(0)

        # calculate completion percent
        completion = (tags.index(tagA) / len(tags)) * 100
        if completion % 10 <= 1:
            logger.info("[STATS] Tag associations %.0f percent complete...",completion)

async def global_stat_calc_loop(interval_mins: float):
    await asyncio.sleep(1)
    while True:
        dbSes = Session(engine)

        totalEntries = query_number(dbSes, select(func.count()).where(DreamEntry.public))
        logger.info("[STATS] Beginning statistics calculation based on %d public entries...", totalEntries)

        await calculate_tag_associations(dbSes)
        await calculate_general_stats(dbSes)
        dbSes.commit()
        dbSes.close()
        
        logger.info("[STATS] Statistics calculation complete.")

        # attempt to recalculate after the specified interval, but only if there are new entries
        recalculate = False
        while not recalculate:
            await asyncio.sleep(60 * interval_mins)
            latest = dbSes.execute(select(func.max(DreamEntry.created_at))).first()
            if latest and latest[0] and latest[0] >= datetime.now() - timedelta(minutes=interval_mins):
                recalculate = True