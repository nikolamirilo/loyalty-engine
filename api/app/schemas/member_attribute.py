from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import Field

from app.models.enums import MemberAttributeType
from app.schemas.base import CamelModel


class MemberAttributeCreate(CamelModel):
    label: str = Field(min_length=1, max_length=100)
    type: MemberAttributeType
    options: Optional[List[str]] = None  # `select` only
    default_value: Optional[Any] = None


class MemberAttributeUpdate(CamelModel):
    """`key` and `type` are deliberately absent - both are immutable once created.

    Renaming the key would orphan every stored value; changing the type would
    invalidate them. Labels and defaults stay freely editable.
    """

    label: Optional[str] = Field(default=None, min_length=1, max_length=100)
    options: Optional[List[str]] = None
    default_value: Optional[Any] = None


class MemberAttributeOut(CamelModel):
    id: UUID
    key: str
    label: str
    type: MemberAttributeType
    options: Optional[List[str]] = None
    default_value: Optional[Any] = None
    created_at: datetime
