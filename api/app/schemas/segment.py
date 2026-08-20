from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.schemas.base import CamelModel


class SegmentBase(CamelModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


class SegmentCreate(SegmentBase):
    pass


class SegmentUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class SegmentSummary(SegmentBase):
    """Minimal segment shape embedded in a member."""

    id: UUID


class SegmentOut(SegmentSummary):
    created_at: datetime
    member_count: int = 0


class MemberAssignRequest(CamelModel):
    member_ids: List[UUID]


class MemberAssignResult(CamelModel):
    segment_id: UUID
    assigned: int
    skipped: int
