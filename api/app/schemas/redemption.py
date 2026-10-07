from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.enums import RedemptionSource
from app.schemas.base import CamelModel
from app.schemas.program import ProgramOut
from app.schemas.reward import RewardOut


class RedemptionOut(CamelModel):
    id: UUID
    member_id: UUID
    reward_id: UUID
    points_spent: int
    source: RedemptionSource
    reward: RewardOut
    created_at: datetime
    # Set once the member claims an assigned prize; null until then.
    claimed_at: Optional[datetime] = None


class PrizeAssignRequest(CamelModel):
    # Email the member about the prize, with a link to claim it in the member app.
    send_email: bool = False


class PrizeAssignOut(RedemptionOut):
    # Whether the prize email went out. The prize is assigned either way: a
    # failed email never undoes it, so `email_error` says what went wrong.
    email_sent: bool = False
    email_error: Optional[str] = None


class PrizeClaimRequest(CamelModel):
    token: str


class PrizeClaimOut(CamelModel):
    """An emailed prize as its claim page sees it.

    `program` is the prize's own program, worked out from the token, so the
    page can wear the right brand without the caller naming one.
    """

    redemption_id: UUID
    reward: RewardOut
    program: ProgramOut
    member_name: str
    claimed_at: Optional[datetime] = None
    expires_at: datetime
    expired: bool
