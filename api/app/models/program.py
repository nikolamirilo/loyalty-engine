import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Program(Base):
    """One isolated loyalty program.

    A program owns its rewards, products, challenges, tiers, segments and
    custom attribute definitions. Rows never move between programs and no
    query spans two of them, so one demo dataset can never show up inside
    another.

    Member *identity* is the deliberate exception: a person exists once
    (``MemberIdentity``) and holds a separate ``Member`` row, with its own
    points and tier, in each program they joined.
    """

    __tablename__ = "programs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # Human-readable handle, accepted in place of the id in the X-Program-Id
    # header so a curl example or an MCP call reads as "coffee-club". Derived
    # from the name on create unless the caller supplies one.
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # The program a request without an X-Program-Id header falls back to.
    # At most one row may set this (enforced by a partial unique index).
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
