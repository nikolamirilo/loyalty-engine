from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelModel


class RewardCreate(CamelModel):
    name: str
    description: Optional[str] = None
    points_cost: int = Field(gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    is_active: bool = True


class RewardUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    points_cost: Optional[int] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class RewardOut(RewardCreate):
    id: UUID
    created_at: datetime
