from datetime import datetime
from uuid import UUID

from app.models.enums import RedemptionSource
from app.schemas.base import CamelModel
from app.schemas.reward import RewardOut


class RedemptionOut(CamelModel):
    id: UUID
    member_id: UUID
    reward_id: UUID
    points_spent: int
    source: RedemptionSource
    reward: RewardOut
    created_at: datetime
