import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TransactionType(str, enum.Enum):
    earn = "earn"
    spend = "spend"
    adjust = "adjust"


class RedemptionSource(str, enum.Enum):
    redeemed = "redeemed"
    assigned = "assigned"


class ChallengeStatus(str, enum.Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    expired = "expired"
    cancelled = "cancelled"


class Tier(Base):
    __tablename__ = "tiers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    min_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    members: Mapped[List["Member"]] = relationship("Member", back_populates="tier", passive_deletes=True)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    segments: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tier_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    tier: Mapped[Optional["Tier"]] = relationship("Tier", back_populates="members")
    transactions: Mapped[List["PointsTransaction"]] = relationship("PointsTransaction", back_populates="member", order_by="PointsTransaction.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    redemptions: Mapped[List["Redemption"]] = relationship("Redemption", back_populates="member", order_by="Redemption.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    challenge_assignments: Mapped[List["ChallengeAssignment"]] = relationship("ChallengeAssignment", back_populates="member", order_by="ChallengeAssignment.assigned_at.desc()", cascade="all, delete-orphan", passive_deletes=True)


class PointsTransaction(Base):
    __tablename__ = "points_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    member: Mapped["Member"] = relationship("Member", back_populates="transactions")


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = unlimited
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    redemptions: Mapped[List["Redemption"]] = relationship("Redemption", back_populates="reward")


class Redemption(Base):
    __tablename__ = "redemptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    reward_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("rewards.id"), nullable=False)
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[RedemptionSource] = mapped_column(Enum(RedemptionSource), nullable=False, default=RedemptionSource.redeemed)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    member: Mapped["Member"] = relationship("Member", back_populates="redemptions")
    reward: Mapped["Reward"] = relationship("Reward", back_populates="redemptions")


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
