import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.challenge import ChallengeAssignment
    from app.models.member_identity import MemberIdentity
    from app.models.points import PointsTransaction
    from app.models.purchase import Purchase
    from app.models.redemption import Redemption
    from app.models.segment import Segment
    from app.models.tier import Tier


class Member(Base):
    """A person's membership in one program.

    The person is ``identity``; this row is their standing in a single
    program. The same identity has at most one of these per program, so
    points, tier, purchases and challenge progress are per program while the
    name and email behind them are shared.

    Everything that hangs off a member (transactions, redemptions,
    purchases, challenge assignments, segment memberships) points at this
    row, which is what keeps that history inside one program without needing
    a `program_id` of its own.
    """

    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("member_identities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tier_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Values for the admin-defined fields in `member_attributes`, keyed by their
    # `key`. Plain JSONB isn't change-tracked, so writes must *reassign* the dict
    # (`member.custom_attributes = {**old, **patch}`) - mutating it in place
    # produces a successful request that silently persists nothing.
    custom_attributes: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    __table_args__ = (UniqueConstraint("program_id", "identity_id", name="uq_program_identity"),)

    identity: Mapped["MemberIdentity"] = relationship("MemberIdentity", back_populates="memberships")
    tier: Mapped[Optional["Tier"]] = relationship("Tier", back_populates="members")
    transactions: Mapped[List["PointsTransaction"]] = relationship("PointsTransaction", back_populates="member", order_by="PointsTransaction.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    redemptions: Mapped[List["Redemption"]] = relationship("Redemption", back_populates="member", order_by="Redemption.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    purchases: Mapped[List["Purchase"]] = relationship("Purchase", back_populates="member", order_by="Purchase.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    challenge_assignments: Mapped[List["ChallengeAssignment"]] = relationship("ChallengeAssignment", back_populates="member", order_by="ChallengeAssignment.assigned_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    segment_assignments: Mapped[List["MemberSegment"]] = relationship("MemberSegment", back_populates="member", cascade="all, delete-orphan", passive_deletes=True)

    # The person's own fields live on the identity, shared across programs.
    # These read-throughs keep `MemberOut` (and every other `from_attributes`
    # read) working unchanged. They are deliberately read-only: a write goes
    # to `member.identity`, so that changing a name in one program changes it
    # everywhere, which is the point of a shared identity.
    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def email(self) -> str:
        return self.identity.email

    @property
    def phone(self) -> Optional[str]:
        return self.identity.phone

    @property
    def email_verified_at(self) -> Optional[datetime]:
        return self.identity.email_verified_at

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
