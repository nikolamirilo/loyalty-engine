from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelModel


class ProductCreate(CamelModel):
    name: str
    description: Optional[str] = None
    price_cents: int = Field(gt=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    category: Optional[str] = None
    is_active: bool = True


class ProductUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_cents: Optional[int] = Field(default=None, gt=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    category: Optional[str] = None
    is_active: Optional[bool] = None


class ProductOut(ProductCreate):
    id: UUID
    created_at: datetime
