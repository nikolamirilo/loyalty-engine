import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import Member


class Tier(Base):
    __tablename__ = "tiers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Unique per program, not globally: two demo programs may each want a
    # tier called Gold, with different thresholds.
    name: Mapped[str] = mapped_column(String, nullable=False)
    min_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    __table_args__ = (UniqueConstraint("program_id", "name", name="uq_program_tier_name"),)

    members: Mapped[List["Member"]] = relationship("Member", back_populates="tier", passive_deletes=True)
