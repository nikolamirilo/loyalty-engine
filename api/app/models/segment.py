import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import MemberSegment


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Unique per program, not globally: "VIP" means something different in
    # each demo dataset and both must be able to exist.
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # UI accent, e.g. "#22c55e"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("program_id", "name", name="uq_program_segment_name"),)

    member_assignments: Mapped[List["MemberSegment"]] = relationship("MemberSegment", back_populates="segment", cascade="all, delete-orphan", passive_deletes=True)

    @property
    def member_count(self) -> int:
        return len(self.member_assignments)
