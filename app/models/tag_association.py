from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import Tag

class TagAssociation(Base):
    __tablename__ = "tag_associations"

    tag_id_a: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)
    tag_id_b: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)
    association_day: Mapped[float] = mapped_column(index=True)
    association_week: Mapped[float] = mapped_column(index=True)
    association_month: Mapped[float] = mapped_column(index=True)
    association_all: Mapped[float] = mapped_column(index=True)

    tag_a: Mapped["Tag"] = relationship(foreign_keys=[tag_id_a])
    tag_b: Mapped["Tag"] = relationship(foreign_keys=[tag_id_b])