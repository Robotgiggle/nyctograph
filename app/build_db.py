from sqlalchemy.orm import Session

from .models import *
from .database import Base, engine
from .utils import ph

# Run this with 'python -m app.build_db' from outside the app folder to avoid relative import errors

def main():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as ses:
        ses.add(User(username="admin", pw_hash=ph.hash("dream"), public_enabled=True))
        ses.commit()

if __name__ == "__main__":
    main()