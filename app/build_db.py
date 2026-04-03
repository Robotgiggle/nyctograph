from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import *
from .database import Base, engine
from .utils import ph

# Run this with 'python -m app.build_db' from outside the app folder to avoid relative import errors

content = [
    "Flying", "Falling", "Paralysis", "Chase", "Embarrassment", "Driving", "School", "Teeth", "Disaster",
    "Monster", "Family", "Romance", "Death", "Sex", "Food", "Betrayal", "Revenge", "Transformation",
    "Naked", "Lost", "Unprepared", "Searching", "Lateness", "Wealth", "Water", "Fire", "Bathroom", 
    "Hospital", "Workplace", "Adventure", "Video Game", "Abstract"
]

types = ["Nightmare", "Recurring", "Lucid", "False Awakening", "Sleep Paralysis"]

contexts = [
    "High Stress", "Illness (Self)", "Illness (Other)", "Pregnancy", "Upcoming Deadline", "Political Change", 
    "Vacation", "Graduation", "Job Interview", "Daytime Nap", "Scary Media", "New Relationship", "New Job",
    "New Child", "New Living Place", "Recent Argument", "Recent Breakup", "Lost Job", "Recent Death", 
    "Natural Disaster", "Major Injury"
]

def main():
    with Session(engine) as ses:
        ses.execute(text("DROP VIEW IF EXISTS research_entries"))
        ses.commit()
    Base.metadata.drop_all(engine)
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
        ses.add(User(username="admin", pw_hash=ph.hash("dream"), email="fake@fake.com", public_enabled=True))
        ses.commit()

if __name__ == "__main__":
    main()