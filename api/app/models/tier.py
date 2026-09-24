import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import Member


class Tier(Base):
    """A point-earning tier a member can be assigned to.

    Eligibility is a list of conditions - ANDed, the same "no OR, no nesting"
    rule an event rule's conditions follow - checked against the same field
    language: points balance, lifetime purchase spend, segments and custom
    attributes (``app.services.rules.fields.tier_fields``). Combining more
    than one is how a program expresses "spend €200 AND hold 500 points" as
    one tier rather than needing a rule engine of its own.

    ``rank`` replaces the old single ``min_points`` ordering: with several
    independent conditions there is no longer one number every tier can be
    sorted by, so an admin sets it explicitly. ``apply_tier`` tries tiers from
    the highest rank down and assigns the first whose conditions all match.
    """

    __tablename__ = "tiers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Unique per program, not globally: two demo programs may each want a
    # tier called Gold, with different thresholds.
    name: Mapped[str] = mapped_column(String, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conditions: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("program_id", "name", name="uq_program_tier_name"),)

    members: Mapped[List["Member"]] = relationship("Member", back_populates="tier", passive_deletes=True)
