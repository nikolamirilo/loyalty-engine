import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MemberAttribute(Base):
    """An admin-defined custom field on members.

    This is the registry the admin console renders from; the values live in
    ``Member.custom_attributes`` keyed by ``key``. Defining a field inserts a row
    here - it never alters the ``members`` table.

    ``key`` and ``type`` are immutable once created: renaming the key would orphan
    every stored value, and changing the type would invalidate them.
    """

    __tablename__ = "member_attributes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    # Stored as a plain string rather than a DB enum so adding a type later needs
    # no migration; the allowed values are enforced in
    # app/services/custom_attributes.py.
    type: Mapped[str] = mapped_column(String, nullable=False)
    options: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)  # `select` only
    default_value: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
