from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import Researcher

class DownloadRecord(Base):
    __tablename__ = "download_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    researcher_id: Mapped[int] = mapped_column(ForeignKey("researchers.id"))
    downloaded_at: Mapped[datetime]
    filters_used: Mapped[str]

    researcher: Mapped[Researcher] = relationship(back_populates="downloads")