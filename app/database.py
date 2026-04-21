from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Setup for PostgreSQL database connection

engine = create_engine(settings.DATABASE_URL)

class Base(DeclarativeBase):
    pass