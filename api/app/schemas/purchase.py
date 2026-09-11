from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelModel


class PurchaseCreate(CamelModel):
    product_id: UUID
    quantity: int = Field(default=1, gt=0)


class PurchaseOut(CamelModel):
    id: UUID
    member_id: UUID
    product_id: Optional[UUID] = None
    product_name: str
    quantity: int
    unit_price_cents: int
    total_cents: int
    currency: str
    created_at: datetime


class PurchaseStatsOut(CamelModel):
    """Spend and frequency signals for one member, used by gamification
    campaigns to personalise the experience.

    ``period_days`` is the window the ``period*`` fields were computed over
    (as requested via ``?days=``); the other fields are lifetime totals so a
    caller doesn't need a second request to get both.
    """

    member_id: UUID
    currency: str = "EUR"

    purchase_count: int = 0
    total_spend_cents: int = 0
    average_order_value_cents: int = 0
    first_purchase_at: Optional[datetime] = None
    last_purchase_at: Optional[datetime] = None
    days_since_last_purchase: Optional[int] = None

    period_days: int
    period_purchase_count: int = 0
    period_spend_cents: int = 0
