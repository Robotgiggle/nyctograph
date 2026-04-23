from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

# Represents a request by a potential client to create a research account
class ResearchRequest(Base):
    __tablename__ = "research_requests"
    __table_args__ = (
        CheckConstraint("status IN ('Pending', 'Approved')"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    ror_id: Mapped[str]
    reason: Mapped[str]
    status: Mapped[str]
    token: Mapped[str|None] = mapped_column(index=True)