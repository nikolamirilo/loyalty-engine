from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import RedemptionSource
from app.schemas.reward import RewardOut


class RedemptionOut(BaseModel):
    id: UUID
    member_id: UUID
    reward_id: UUID
    points_spent: int
    source: RedemptionSource
    reward: RewardOut
    created_at: datetime

    model_config = {"from_attributes": True}
