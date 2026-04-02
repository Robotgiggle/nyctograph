from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import Tag, GlobalStats

class TagAssociation(Base):
    __tablename__ = "tag_associations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["time_slice","age_bracket"],
            ["global_stats.time_slice","global_stats.age_bracket"]
        ),
    )

    tag_val_a: Mapped[str] = mapped_column(ForeignKey("tags.value"), primary_key=True)
    tag_val_b: Mapped[str] = mapped_column(ForeignKey("tags.value"), primary_key=True)
    time_slice: Mapped[str]
    age_bracket: Mapped[str]
    association_rate: Mapped[float]

    tag_a: Mapped["Tag"] = relationship(foreign_keys=[tag_val_a])
    tag_b: Mapped["Tag"] = relationship(foreign_keys=[tag_val_b])
    stats_obj: Mapped["GlobalStats"] = relationship(back_populates="tag_associations")