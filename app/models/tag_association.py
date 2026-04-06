from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from . import Tag, GlobalStats

#
# The association rate represents "how often is Tag B present on entries that have Tag A?"
# This can also be stated as "to what extent does Tag A imply Tag B?"
#

# positive association if near 1
# negative association if near 0
# neutral association if rate = total B / total entries

# association strength:
# if rate > midpoint, invlerp(midpoint,1,rate)
# if rate < midpoint, -invlerp(-midpoint,0,-rate)

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