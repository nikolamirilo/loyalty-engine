from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import TransactionType


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
