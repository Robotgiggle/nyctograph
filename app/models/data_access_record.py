from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import Researcher

# Created whenever data is requested, to record exactly what data was provided to whom [REQ-6]
class DataAccessRecord(Base):
    __tablename__ = "data_access_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    researcher_id: Mapped[int] = mapped_column(ForeignKey("researchers.id"))
    accessed_at: Mapped[datetime]
    filters_used: Mapped[str]

    researcher: Mapped["Researcher"] = relationship(back_populates="data_accesses")