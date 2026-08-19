import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TransactionType

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import Member


class PointsTransaction(Base):
    __tablename__ = "points_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    member: Mapped["Member"] = relationship("Member", back_populates="transactions")
