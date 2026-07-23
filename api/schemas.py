from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from models import ChallengeStatus, RedemptionSource, TransactionType


# ── Tier ──────────────────────────────────────────────────────────────────────

class TierBase(BaseModel):
    name: str
    min_points: int = Field(ge=0)
    multiplier: float = Field(gt=0, default=1.0)


class TierCreate(TierBase):
    pass


class TierOut(TierBase):
    id: UUID

    model_config = {"from_attributes": True}


# ── Segment ───────────────────────────────────────────────────────────────────

class SegmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


class SegmentCreate(SegmentBase):
    pass


class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class SegmentSummary(SegmentBase):
    """Minimal segment shape embedded in a member."""

    id: UUID

    model_config = {"from_attributes": True}


class SegmentOut(SegmentSummary):
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


# ── Member ────────────────────────────────────────────────────────────────────

class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    segment_ids: List[UUID] = Field(default_factory=list)


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    segment_ids: Optional[List[UUID]] = None


class MemberOut(BaseModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    segments: List[SegmentSummary] = Field(default_factory=list)
    pointsBalance: int = Field(validation_alias="total_points", serialization_alias="pointsBalance")

    model_config = {"from_attributes": True, "populate_by_name": True}


# ── Points ────────────────────────────────────────────────────────────────────

class EarnPointsRequest(BaseModel):
    points: int = Field(gt=0)
    description: Optional[str] = None


class SpendPointsRequest(BaseModel):
    points: int = Field(gt=0)
    description: Optional[str] = None


class AdjustPointsRequest(BaseModel):
    points: int  # can be negative
    description: Optional[str] = None


class PointsTransactionOut(BaseModel):
    id: UUID
    member_id: UUID
    points: int
    type: TransactionType
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class BalanceOut(BaseModel):
    member_id: UUID
    pointsBalance: int


# ── Reward ────────────────────────────────────────────────────────────────────

class RewardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    points_cost: int = Field(gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    is_active: bool = True


class RewardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    points_cost: Optional[int] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class RewardOut(RewardCreate):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Redemption ────────────────────────────────────────────────────────────────

class RedemptionOut(BaseModel):
    id: UUID
    member_id: UUID
    reward_id: UUID
    points_spent: int
    source: RedemptionSource
    reward: RewardOut
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Challenge ─────────────────────────────────────────────────────────────────

class ChallengeBase(BaseModel):
    name: str
    description: Optional[str] = None
    target_value: int = Field(gt=0, default=1)
    reward_points: int = Field(ge=0, default=0)
    reward_id: Optional[UUID] = None
    is_active: bool = True
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ChallengeCreate(ChallengeBase):
    pass


class ChallengeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[int] = Field(default=None, gt=0)
    reward_points: Optional[int] = Field(default=None, ge=0)
    reward_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ChallengeOut(ChallengeBase):
    id: UUID
    created_at: datetime
    segments: List[str] = Field(default_factory=list)  # segments this challenge was bulk-assigned to

    model_config = {"from_attributes": True}


class ChallengeAssignmentOut(BaseModel):
    id: UUID
    challenge_id: UUID
    member_id: UUID
    status: ChallengeStatus
    current_value: int
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    challenge: ChallengeOut

    model_config = {"from_attributes": True}


class ChallengeProgressOut(BaseModel):
    """Challenge info + one member's progress on it, combined."""

    id: UUID
    name: str
    description: Optional[str] = None
    target_value: int
    reward_points: int
    reward_id: Optional[UUID] = None
    is_active: bool
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    is_assigned: bool
    assignment_id: Optional[UUID] = None
    current_value: int = 0
    progress_percent: int = 0
    remaining: int
    is_expired: bool
    effective_status: Optional[ChallengeStatus] = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProgressRequest(BaseModel):
    amount: int = Field(gt=0, default=1)
    description: Optional[str] = None


class SegmentAssignRequest(BaseModel):
    segment_id: UUID


class SegmentAssignResult(BaseModel):
    challenge_id: UUID
    segment_id: UUID
    assigned: int
    skipped: int
