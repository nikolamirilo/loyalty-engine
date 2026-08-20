import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.challenge import ChallengeAssignment
    from app.models.points import PointsTransaction
    from app.models.redemption import Redemption
    from app.models.segment import Segment
    from app.models.tier import Tier


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tier_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # NULL = email not yet verified via the DOI flow (see app/services/email_verification.py).
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Values for the admin-defined fields in `member_attributes`, keyed by their
    # `key`. Plain JSONB isn't change-tracked, so writes must *reassign* the dict
    # (`member.custom_attributes = {**old, **patch}`) - mutating it in place
    # produces a successful request that silently persists nothing.
    custom_attributes: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    tier: Mapped[Optional["Tier"]] = relationship("Tier", back_populates="members")
    transactions: Mapped[List["PointsTransaction"]] = relationship("PointsTransaction", back_populates="member", order_by="PointsTransaction.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    redemptions: Mapped[List["Redemption"]] = relationship("Redemption", back_populates="member", order_by="Redemption.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    challenge_assignments: Mapped[List["ChallengeAssignment"]] = relationship("ChallengeAssignment", back_populates="member", order_by="ChallengeAssignment.assigned_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    segment_assignments: Mapped[List["MemberSegment"]] = relationship("MemberSegment", back_populates="member", cascade="all, delete-orphan", passive_deletes=True)

    @property
    def segments(self) -> List["Segment"]:
        """Segments this member currently belongs to."""
        return [sa.segment for sa in self.segment_assignments]


class MemberSegment(Base):
    """A member's membership in a segment."""

    __tablename__ = "member_segments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("member_id", "segment_id", name="uq_member_segment"),)

    member: Mapped["Member"] = relationship("Member", back_populates="segment_assignments")
    segment: Mapped["Segment"] = relationship("Segment", back_populates="member_assignments")
