from os import getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

# Setup for PostgreSQL database connection

load_dotenv(".env")

engine = create_engine(getenv("DATABASE_URL", ""))

class Base(DeclarativeBase):
    pass