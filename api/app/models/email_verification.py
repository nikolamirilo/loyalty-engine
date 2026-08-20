import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import DOIType


class EmailVerificationCode(Base):
    """A single-use DOI verification code issued for a member's email.

    Stores only a hash of the code (see app/services/email_verification.py),
    never the raw value.
    """

    __tablename__ = "email_verification_codes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String, nullable=False)
    # Which email the member was sent for this code (a typed code vs. a link
    # that verifies for them). Only the hash of the code is stored, so the link
    # can never be rebuilt after the fact - a trigger asking for a different
    # type than the live code has to issue a new code.
    type: Mapped[DOIType] = mapped_column(Enum(DOIType), nullable=False, default=DOIType.code)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
