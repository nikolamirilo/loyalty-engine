import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.redemption import Redemption


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = unlimited
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    redemptions: Mapped[List["Redemption"]] = relationship("Redemption", back_populates="reward")
