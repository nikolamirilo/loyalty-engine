from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelModel
from app.schemas.conditions import RuleCondition


class TierBase(CamelModel):
    name: str
    # Tiers are tried from the highest rank down; a member is assigned to the
    # first tier whose conditions all match. Ties break by creation order
    # (see `app.services.tiers`).
    rank: int = 0
    # All must match - the same "no OR, no nesting" rule as an event rule's
    # conditions: two tiers express an OR. No conditions matches every member,
    # so a tier with none is a catch-all wherever it sits in the rank order
    # (typically the lowest rank, as a default tier).
    conditions: List[RuleCondition] = Field(default_factory=list)
    multiplier: float = Field(gt=0, default=1.0)


class TierCreate(TierBase):
    pass


class TierUpdate(CamelModel):
    name: Optional[str] = None
    rank: Optional[int] = None
    conditions: Optional[List[RuleCondition]] = None
    multiplier: Optional[float] = Field(default=None, gt=0)


class TierOut(TierBase):
    id: UUID
