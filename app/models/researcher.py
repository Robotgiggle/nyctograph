from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import DownloadRecord

class Researcher(Base):
    __tablename__ = "researchers"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True)
    pw_hash: Mapped[str]
    email: Mapped[str]
    ror_id: Mapped[str]
    data_filters: Mapped[str]

    downloads: Mapped[List["DownloadRecord"]] = relationship(back_populates="researcher")