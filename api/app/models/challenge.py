import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ChallengeStatus

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import Member
    from app.models.reward import Reward
    from app.models.segment import Segment


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)   # progress needed to complete
    reward_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # points granted on completion
    reward_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("rewards.id", ondelete="SET NULL"), nullable=True)  # optional prize
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    reward: Mapped[Optional["Reward"]] = relationship("Reward")
    assignments: Mapped[List["ChallengeAssignment"]] = relationship("ChallengeAssignment", back_populates="challenge", cascade="all, delete-orphan", passive_deletes=True)
    segment_assignments: Mapped[List["ChallengeSegmentAssignment"]] = relationship(
        "ChallengeSegmentAssignment",
        back_populates="challenge",
        order_by="ChallengeSegmentAssignment.assigned_at",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def segments(self) -> List[str]:
        """Segment names this challenge has been bulk-assigned to (in assign order)."""
        return [sa.segment.name for sa in self.segment_assignments]


class ChallengeAssignment(Base):
    __tablename__ = "challenge_assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    challenge_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[ChallengeStatus] = mapped_column(Enum(ChallengeStatus), nullable=False, default=ChallengeStatus.assigned)
    current_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("challenge_id", "member_id", name="uq_challenge_member"),)

    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="assignments")
    member: Mapped["Member"] = relationship("Member", back_populates="challenge_assignments")


class ChallengeSegmentAssignment(Base):
    """A segment a challenge has been bulk-assigned to.

    Individual member assignments live in ``challenge_assignments``; this table
    additionally remembers which *segments* were targeted by
    ``POST /challenges/{id}/assign-segment`` so the console can show, per
    challenge, which segments it was pushed to. Segment membership changes over
    time, so this can't be reliably derived from the members' current segments.
    """

    __tablename__ = "challenge_segment_assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    challenge_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("segments.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("challenge_id", "segment_id", name="uq_challenge_segment"),)

    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="segment_assignments")
    segment: Mapped["Segment"] = relationship("Segment")
