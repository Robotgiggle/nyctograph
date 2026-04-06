from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import Tag, GlobalStats

#
# The association rate represents "how often is Tag B present on entries that have Tag A?"
#
# The association strength (between 1 and -1) represents the degree to which the association rate
# varies from the base rate of Tag B. Strength is 0 if rate = total B / total entries.
#

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
    time_slice: Mapped[str] = mapped_column(primary_key=True)
    age_bracket: Mapped[str] = mapped_column(primary_key=True)
    association_rate: Mapped[float]
    association_strength: Mapped[float]

    tag_a: Mapped["Tag"] = relationship(foreign_keys=[tag_val_a])
    tag_b: Mapped["Tag"] = relationship(foreign_keys=[tag_val_b])
    stats_obj: Mapped["GlobalStats"] = relationship(back_populates="tag_associations")