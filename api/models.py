import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
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
from sqlalchemy.orm import relationship

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

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    min_points = Column(Integer, nullable=False, default=0)
    multiplier = Column(Float, nullable=False, default=1.0)

    members = relationship("Member", back_populates="tier", passive_deletes=True)


class Member(Base):
    __tablename__ = "members"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    segments = Column(JSON, nullable=False, default=list)
    total_points = Column(Integer, nullable=False, default=0)
    tier_id = Column(Uuid, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tier = relationship("Tier", back_populates="members")
    transactions = relationship("PointsTransaction", back_populates="member", order_by="PointsTransaction.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    redemptions = relationship("Redemption", back_populates="member", order_by="Redemption.created_at.desc()", cascade="all, delete-orphan", passive_deletes=True)
    challenge_assignments = relationship("ChallengeAssignment", back_populates="member", order_by="ChallengeAssignment.assigned_at.desc()", cascade="all, delete-orphan", passive_deletes=True)


class PointsTransaction(Base):
    __tablename__ = "points_transactions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id = Column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    member = relationship("Member", back_populates="transactions")


class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    points_cost = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=True)  # None = unlimited
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    redemptions = relationship("Redemption", back_populates="reward")


class Redemption(Base):
    __tablename__ = "redemptions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id = Column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    reward_id = Column(Uuid, ForeignKey("rewards.id"), nullable=False)
    points_spent = Column(Integer, nullable=False)
    source = Column(Enum(RedemptionSource), nullable=False, default=RedemptionSource.redeemed)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    member = relationship("Member", back_populates="redemptions")
    reward = relationship("Reward", back_populates="redemptions")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_value = Column(Integer, nullable=False, default=1)   # progress needed to complete
    reward_points = Column(Integer, nullable=False, default=0)  # points granted on completion
    reward_id = Column(Uuid, ForeignKey("rewards.id", ondelete="SET NULL"), nullable=True)  # optional prize
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    reward = relationship("Reward")
    assignments = relationship("ChallengeAssignment", back_populates="challenge", cascade="all, delete-orphan", passive_deletes=True)


class ChallengeAssignment(Base):
    __tablename__ = "challenge_assignments"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    challenge_id = Column(Uuid, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ChallengeStatus), nullable=False, default=ChallengeStatus.assigned)
    current_value = Column(Integer, nullable=False, default=0)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("challenge_id", "member_id", name="uq_challenge_member"),)

    challenge = relationship("Challenge", back_populates="assignments")
    member = relationship("Member", back_populates="challenge_assignments")
