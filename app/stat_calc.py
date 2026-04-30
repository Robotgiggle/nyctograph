import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, delete, desc, func
from sqlalchemy.orm import Session
import logging

from .models import DreamEntry, User, Tag, TagTotal, TagAssociation, GlobalStats
from .database import engine
from .utils import inv_lerp

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

def apply_query_filters(query, daysIncluded, ageBracket):
    # time slice filter
    if daysIncluded:
        cutoffDate = datetime.today() - timedelta(days=daysIncluded) if daysIncluded else datetime.min
        dayFiltered = query.where(DreamEntry.created_at > cutoffDate)
    else:
        dayFiltered = query
    # age bracket filter
    if ageBracket:
        return dayFiltered.where(
            func.extract("day", (func.now() - User.birth_date)/365.25) > ageBracket[0],
            func.extract("day", (func.now() - User.birth_date)/365.25) < ageBracket[1]
        )
    else:
        return dayFiltered

async def calculate_general_stats(dbSes: Session):
    # build the two queries
    baseSleepSubq = (
        select(func.avg(DreamEntry.sleep_hours).label("per_user"))
        .join(User).where(DreamEntry.public == True)
        .group_by(DreamEntry.user_id)
    )
    baseStatQuery = select(
        func.count(), 
        func.count().filter(DreamEntry.sense_sight == True), 
        func.count().filter(DreamEntry.sense_sound == True), 
        func.count().filter(DreamEntry.sense_touch == True), 
        func.count().filter(DreamEntry.sense_smell == True), 
        func.count().filter(DreamEntry.sense_taste == True), 
        func.count().filter(DreamEntry.sense_pain == True), 
        func.count().filter(DreamEntry.sense_other == True), 
    ).join(User).where(DreamEntry.public == True)

    # calculate new global stats, across four time periods and four age brackets
    for daysIncluded in [1, 7, 30, None]:
        for ageBracket in [(13,29), (30,49), (50,999), None]:
            statQueryFiltered = apply_query_filters(baseStatQuery, daysIncluded, ageBracket)
            sleepSubqFiltered = apply_query_filters(baseSleepSubq, daysIncluded, ageBracket).subquery()

            statResults = dbSes.execute(statQueryFiltered).first()
            fullSleepQuery = select(func.coalesce(func.avg(sleepSubqFiltered.c.per_user), 0))
            avgSleep = dbSes.scalar(fullSleepQuery) or 0

            newStatsObj = GlobalStats(
                time_slice = {1: "day", 7: "week", 30: "month", None: "all"}[daysIncluded],
                age_bracket = {(13,29): "13-29", (30,49): "30-49", (50,999): "50+", None: "all"}[ageBracket],
                total_entries = statResults[0] if statResults else 0,
                sight_rate = statResults[1]/statResults[0] if statResults and statResults[0] else 0,
                sound_rate = statResults[2]/statResults[0] if statResults and statResults[0] else 0,
                touch_rate = statResults[3]/statResults[0] if statResults and statResults[0] else 0,
                smell_rate = statResults[4]/statResults[0] if statResults and statResults[0] else 0,
                taste_rate = statResults[5]/statResults[0] if statResults and statResults[0] else 0,
                pain_rate = statResults[6]/statResults[0] if statResults and statResults[0] else 0,
                other_rate = statResults[7]/statResults[0] if statResults and statResults[0] else 0,
                avg_sleep_duration = avgSleep
            )
            dbSes.add(newStatsObj)

            # yield to the event loop to allow request handling mid-calculation
            await asyncio.sleep(0)

        # calculate completion percent
        completion = 25 * [1, 7, 30, None].index(daysIncluded)
        logger.info("[STATS] General statistics %.0f percent complete...", completion)
    logger.info("[STATS] General statistics complete.")

async def calculate_tag_totals(dbSes: Session):
    # build the base query
    baseTagQuery = (
        select(Tag.value, Tag.category, func.count().label("total"))
        .join(Tag, DreamEntry.tags).join(User)
        .where(DreamEntry.public == True)
        .group_by(Tag.value)
    )

    # loop across four time periods and four age brackets
    for daysIncluded in [1, 7, 30, None]:
        for ageBracket in [(13,29), (30,49), (50,999), None]:
            tqFiltered = apply_query_filters(baseTagQuery, daysIncluded, ageBracket)
            tagCounts = dbSes.execute(tqFiltered).all()
            
            for row in tagCounts:
                newTotal = TagTotal(
                    tag_val = row[0],
                    tag_cat = row[1],
                    time_slice = {1: "day", 7: "week", 30: "month", None: "all"}[daysIncluded],
                    age_bracket = {(13,29): "13-29", (30,49): "30-49", (50,999): "50+", None: "all"}[ageBracket],
                    total = row[2]
                )
                dbSes.add(newTotal)
            
            # yield to the event loop to allow request handling mid-calculation
            await asyncio.sleep(0)

        # calculate completion percent
        completion = 25 * [1, 7, 30, None].index(daysIncluded)
        logger.info("[STATS] Tag totals %.0f percent complete...", completion)
    logger.info("[STATS] Tag totals complete.")

async def calculate_tag_associations(dbSes: Session):
    # calculate new tag associations
    tags = dbSes.scalars(select(Tag)).all()
    for tagA in tags:
        for tagB in tags:
            # don't compare tags in the same category
            if tagA.category == tagB.category: continue

            # build the base forms of the three queries
            queryA = select(DreamEntry.id).join_from(DreamEntry, User).where(
                DreamEntry.public, 
                DreamEntry.tags.any(Tag.value == tagA.value)
            )
            queryB = select(DreamEntry.id).join_from(DreamEntry, User).where(
                DreamEntry.public, 
                DreamEntry.tags.any(Tag.value == tagB.value)
            )
            queryTotal = select(func.count()).join_from(DreamEntry, User).where(DreamEntry.public)

            # loop across four time periods and four age brackets
            for daysIncluded in [1, 7, 30, None]:
                for ageBracket in [(13,29), (30,49), (50,999), None]:
                    queryAFiltered = apply_query_filters(queryA, daysIncluded, ageBracket)
                    queryBFiltered = apply_query_filters(queryB, daysIncluded, ageBracket)
                    queryTotalFiltered = apply_query_filters(queryTotal, daysIncluded, ageBracket)
                    entriesA = dbSes.execute(queryAFiltered).all()
                    entriesB = dbSes.execute(queryBFiltered).all()
                    totalEntries = dbSes.scalar(queryTotalFiltered)
                    if not entriesA or not entriesB or not totalEntries: continue

                    # rate = "how often is Tag B present on entries that have Tag A?"
                    rate = len(set(entriesA) & set(entriesB)) / len(entriesA)
                    
                    # strength = "how different is this rate from the base rate of Tag B?"
                    baseRate = len(entriesB) / totalEntries
                    if baseRate == rate == 1: 
                        strength = 1
                    elif rate >= baseRate: 
                        strength = inv_lerp(baseRate, 1, rate)
                    else:
                        strength = -1*inv_lerp(-1*baseRate, 0, -1*rate)

                    newAssociation = TagAssociation(
                        tag_a = tagA,
                        tag_b = tagB,
                        time_slice = {1: "day", 7: "week", 30: "month", None: "all"}[daysIncluded],
                        age_bracket = {(13,29): "13-29", (30,49): "30-49", (50,999): "50+", None: "all"}[ageBracket],
                        association_rate = rate,
                        association_strength = strength
                    )
                    dbSes.add(newAssociation)

                # yield to the event loop to allow request handling mid-calculation
                await asyncio.sleep(0)

        # calculate completion percent
        completion = (tags.index(tagA) / len(tags)) * 100
        if completion % 10 < 1:
            logger.info("[STATS] Tag associations %.0f percent complete...",completion)
    logger.info("[STATS] Tag associations complete.")

# Periodically calculates a variety of statistics from all public dream entries [REQ-4]
async def global_stat_calc_loop(interval_mins: float):
    await asyncio.sleep(1)
    while True:
        dbSes = Session(engine)
        try:
            totalEntries = dbSes.scalar(select(func.count()).where(DreamEntry.public)) or 0
            logger.info("[STATS] Beginning statistics calculation based on %d public entries...", totalEntries)

            # delete the data from the last calculation run
            dbSes.execute(delete(TagTotal))
            dbSes.execute(delete(TagAssociation))
            dbSes.execute(delete(GlobalStats))
            
            # calculate new data
            await calculate_general_stats(dbSes)
            await calculate_tag_totals(dbSes)
            await calculate_tag_associations(dbSes)
            
            # commit the transaction only once everything is done
            dbSes.commit()
            dbSes.close()
            
            logger.info("[STATS] Statistics calculation complete.")
        except asyncio.CancelledError as err:
            dbSes.rollback()
            dbSes.close()
            logger.warning("[STATS] Calculation cancelled.")
            raise err
        
        # attempt to recalculate after the specified interval, but only if there are new entries
        recalculate = False
        while not recalculate:
            await asyncio.sleep(60 * interval_mins)
            latest = dbSes.execute(select(func.max(DreamEntry.created_at))).first()
            if latest and latest[0] and latest[0] >= datetime.now() - timedelta(minutes=interval_mins):
                recalculate = True
