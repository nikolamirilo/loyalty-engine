from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.segment import SegmentSummary


class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    segment_ids: List[UUID] = Field(default_factory=list)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    segment_ids: Optional[List[UUID]] = None
    # Omit to leave custom attributes untouched. When present, the map is merged
    # into the stored one (one level deep), so a caller that knows about a single
    # attribute can't wipe the others; a key sent as null clears that one value.
    custom_attributes: Optional[Dict[str, Any]] = None
    # Admin override of DOI status: true stamps email_verified_at with now, false
    # clears it. Omit to leave verification status untouched (the normal path is
    # the /doi/verify flow, not this field).
    email_verified: Optional[bool] = None


class MemberOut(BaseModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    segments: List[SegmentSummary] = Field(default_factory=list)
    pointsBalance: int = Field(validation_alias="total_points", serialization_alias="pointsBalance")
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)
    email_verified_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "populate_by_name": True}
