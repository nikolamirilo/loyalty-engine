from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import EmailStr, Field, computed_field

from app.schemas.base import CamelModel
from app.schemas.segment import SegmentSummary


class MemberCreate(CamelModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    segment_ids: List[UUID] = Field(default_factory=list)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class MemberUpdate(CamelModel):
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


class MemberOut(CamelModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    segments: List[SegmentSummary] = Field(default_factory=list)
    points_balance: int = Field(validation_alias="total_points")
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)
    email_verified_at: Optional[datetime] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None
