from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.enums import TransactionType
from app.schemas.base import CamelModel


class EarnPointsRequest(CamelModel):
    points: int = Field(gt=0)
    description: Optional[str] = None


class SpendPointsRequest(CamelModel):
    points: int = Field(gt=0)
    description: Optional[str] = None


class AdjustPointsRequest(CamelModel):
    points: int  # can be negative
    description: Optional[str] = None


class PointsTransactionOut(CamelModel):
    id: UUID
    member_id: UUID
    points: int
    type: TransactionType
    description: Optional[str]
    created_at: datetime


class BalanceOut(CamelModel):
    member_id: UUID
    points_balance: int
