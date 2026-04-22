from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
import logging

from .models import *
from .database import Base, engine
from .utils import ph
from .config import settings

# Run this with 'python -m app.build_db' from outside the app folder to avoid relative import errors

content = [
    "Flying", "Falling", "Paralysis", "Chase", "Embarrassment", "Driving", "School", "Teeth", "Disaster",
    "Monster", "Family", "Romance", "Death", "Sex", "Food", "Youth", "Old Age", "Betrayal", "Revenge", 
    "Transformation", "Naked", "Lost", "Unprepared", "Searching", "Lateness", "Wealth", "Water", "Fire", 
    "Bathroom", "Hospital", "Workplace", "Adventure", "Video Game", "Abstract"
]

types = ["Nightmare", "Recurring", "Lucid", "False Awakening", "Sleep Paralysis"]

contexts = [
    "High Stress", "Illness (Self)", "Illness (Other)", "Money Issues", "Upcoming Deadline", "Pregnancy", 
    "Political Change", "Vacation", "Graduation", "Marriage", "Holiday", "Birthday", "Job Interview", 
    "Scary Media", "In Love", "New Relationship", "New Job", "New Child", "New Living Place", "Rejection",
    "Recent Argument", "Recent Breakup", "Lost Job", "Recent Death", "Natural Disaster", "Major Injury"
]

calcs = [
    "Short Sleep", "Very Short Sleep", "Long Sleep", "Daytime Sleep", "Atypical Location"
]

logger = logging.getLogger("uvicorn")

def build_db(skip_if_exists: bool):    
    insp = inspect(engine)
    exists = insp.has_table("users")
    
    if skip_if_exists and exists:
        logger.info("[BUILD-DB] Database has already been built, no action necessary.")
        return
    elif exists:
        logger.info("[BUILD-DB] Starting database rebuild...")
    else:
        logger.info("[BUILD-DB] Starting database build...")
    
    # Postgres: drop_all() can fail when leftover tables/views/constraints exist outside
    # SQLAlchemy metadata (e.g. old migrations). Reset the public schema for a clean dev DB.
    with Session(engine) as ses:
        ses.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        ses.execute(text("CREATE SCHEMA public"))
        ses.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        ses.execute(text("GRANT ALL ON SCHEMA public TO public"))
        ses.commit()
    Base.metadata.create_all(engine)
    with Session(engine) as ses:
        with open("app/research_entries_view.sql") as file:
            ses.execute(text(file.read()))
        for item in content:
            ses.add(Tag(category="dream_content", value=item))
        for item in types:
            ses.add(Tag(category="dream_type", value=item))
        for item in contexts:
            ses.add(Tag(category="irl_context", value=item))
        for item in calcs:
            ses.add(Tag(category="calculated", value=item))
        ses.add(User(
            username="admin", 
            pw_hash=ph.hash(settings.ADMIN_ACCOUNT_PW), 
            email="admin@nyctograph.org", 
            public_enabled=True
        ))
        ses.add(Researcher(
            name="Research Admin",
            username="resAdmin",
            pw_hash=ph.hash(settings.ADMIN_ACCOUNT_PW), 
            email="admin@nyctograph.org", 
            ror_id="0190ak572",
            inst_name="New York University"
        ))
        ses.commit()

    logger.info("[BUILD-DB] Database is ready.")

if __name__ == "__main__":
    build_db(skip_if_exists=False)