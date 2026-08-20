from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelModel


class TierBase(CamelModel):
    name: str
    min_points: int = Field(ge=0)
    multiplier: float = Field(gt=0, default=1.0)


class TierCreate(TierBase):
    pass


class TierUpdate(CamelModel):
    name: Optional[str] = None
    min_points: Optional[int] = Field(default=None, ge=0)
    multiplier: Optional[float] = Field(default=None, gt=0)


class TierOut(TierBase):
    id: UUID
