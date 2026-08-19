import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RedemptionSource

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import Member
    from app.models.reward import Reward


class Redemption(Base):
    __tablename__ = "redemptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    reward_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("rewards.id"), nullable=False)
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[RedemptionSource] = mapped_column(Enum(RedemptionSource), nullable=False, default=RedemptionSource.redeemed)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    member: Mapped["Member"] = relationship("Member", back_populates="redemptions")
    reward: Mapped["Reward"] = relationship("Reward", back_populates="redemptions")
