from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
