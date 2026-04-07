from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

# Setup for PostgreSQL database connection

class Base(DeclarativeBase):
    pass

engine = create_engine("postgresql://postgres:opensesame@localhost:5432/nyctograph")