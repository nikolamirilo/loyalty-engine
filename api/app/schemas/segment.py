from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


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


class MemberAssignRequest(BaseModel):
    member_ids: List[UUID]


class MemberAssignResult(BaseModel):
    segment_id: UUID
    assigned: int
    skipped: int
