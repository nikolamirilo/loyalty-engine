from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.models.enums import ChallengeStatus
from app.schemas.base import CamelModel


class ChallengeBase(CamelModel):
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


class ChallengeUpdate(CamelModel):
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


class ChallengeAssignmentOut(CamelModel):
    id: UUID
    challenge_id: UUID
    member_id: UUID
    status: ChallengeStatus
    current_value: int
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    challenge: ChallengeOut


class ChallengeProgressOut(CamelModel):
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


class ProgressRequest(CamelModel):
    amount: int = Field(gt=0, default=1)
    description: Optional[str] = None


class SegmentAssignRequest(CamelModel):
    segment_id: UUID


class SegmentAssignResult(CamelModel):
    challenge_id: UUID
    segment_id: UUID
    assigned: int
    skipped: int
