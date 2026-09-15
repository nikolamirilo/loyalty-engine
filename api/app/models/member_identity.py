import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import Member


class MemberIdentity(Base):
    """A person, independent of any program.

    One email address is one identity. The same person can hold a membership
    in several programs; their points, tier, purchases and challenge progress
    live on those memberships (``Member``), never here.

    Email verification is identity level on purpose: proving an address once
    proves it for the person, so a member verified in one program is verified
    in all of them.
    """

    __tablename__ = "member_identities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # NULL = email not yet verified via the DOI flow (see app/services/email_verification.py).
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    memberships: Mapped[List["Member"]] = relationship(
        "Member", back_populates="identity", cascade="all, delete-orphan", passive_deletes=True
    )
