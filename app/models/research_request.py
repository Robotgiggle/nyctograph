from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

class ResearchRequest(Base):
    __tablename__ = "research_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    ror_id: Mapped[str]
    reason: Mapped[str]