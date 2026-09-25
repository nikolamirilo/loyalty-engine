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
    # Branding for demos: the console and the member app both take on the
    # selected program's logo and colours. All optional - a program without
    # them keeps the stock look. Colours are "#rrggbb"; the logo is a public
    # URL in the Supabase Storage bucket (app.services.storage), only ever set
    # by the upload endpoint so it always points at a file we own.
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
