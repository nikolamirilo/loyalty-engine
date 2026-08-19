import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import MemberSegment


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # UI accent, e.g. "#22c55e"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    member_assignments: Mapped[List["MemberSegment"]] = relationship("MemberSegment", back_populates="segment", cascade="all, delete-orphan", passive_deletes=True)

    @property
    def member_count(self) -> int:
        return len(self.member_assignments)
