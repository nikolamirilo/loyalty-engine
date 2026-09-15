"""Pydantic request/response schemas, grouped by domain.

Re-exported here so routers can import from one place, mirroring how
``app.models`` works.
"""

from app.schemas.auth import (
    AuthLoginRequest,
    AuthSignupRequest,
    AuthTriggerResponse,
    AuthVerifyRequest,
    AuthVerifyResponse,
)
from app.schemas.challenge import (
    ChallengeAssignmentOut,
    ChallengeBase,
    ChallengeCreate,
    ChallengeOut,
    ChallengeProgressOut,
    ChallengeUpdate,
    ProgressRequest,
    SegmentAssignRequest,
    SegmentAssignResult,
)
from app.schemas.email_verification import (
    DOITriggerRequest,
    DOITriggerResponse,
    DOIVerifyRequest,
    DOIVerifyResponse,
)
from app.schemas.member import (
    MemberCountOut,
    MemberCreate,
    MemberOut,
    MemberStatsOut,
    MemberUpdate,
)
from app.schemas.member_attribute import (
    MemberAttributeCreate,
    MemberAttributeOut,
    MemberAttributeUpdate,
)
from app.schemas.points import (
    AdjustPointsRequest,
    BalanceOut,
    EarnPointsRequest,
    PointsTransactionOut,
    SpendPointsRequest,
)
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.schemas.program import ProgramCreate, ProgramOut, ProgramUpdate
from app.schemas.purchase import PurchaseCreate, PurchaseOut, PurchaseStatsOut
from app.schemas.redemption import RedemptionOut
from app.schemas.reward import RewardCreate, RewardOut, RewardUpdate
from app.schemas.segment import (
    MemberAssignRequest,
    MemberAssignResult,
    SegmentBase,
    SegmentCreate,
    SegmentOut,
    SegmentSummary,
    SegmentUpdate,
)
from app.schemas.tier import TierBase, TierCreate, TierOut, TierUpdate

__all__ = [
    "AdjustPointsRequest",
    "AuthLoginRequest",
    "AuthSignupRequest",
    "AuthTriggerResponse",
    "AuthVerifyRequest",
    "AuthVerifyResponse",
    "BalanceOut",
    "ChallengeAssignmentOut",
    "ChallengeBase",
    "ChallengeCreate",
    "ChallengeOut",
    "ChallengeProgressOut",
    "ChallengeUpdate",
    "DOITriggerRequest",
    "DOITriggerResponse",
    "DOIVerifyRequest",
    "DOIVerifyResponse",
    "EarnPointsRequest",
    "MemberAssignRequest",
    "MemberAssignResult",
    "MemberAttributeCreate",
    "MemberAttributeOut",
    "MemberAttributeUpdate",
    "MemberCountOut",
    "MemberCreate",
    "MemberOut",
    "MemberStatsOut",
    "MemberUpdate",
    "PointsTransactionOut",
    "ProductCreate",
    "ProductOut",
    "ProductUpdate",
    "ProgramCreate",
    "ProgramOut",
    "ProgramUpdate",
    "ProgressRequest",
    "PurchaseCreate",
    "PurchaseOut",
    "PurchaseStatsOut",
    "RedemptionOut",
    "RewardCreate",
    "RewardOut",
    "RewardUpdate",
    "SegmentAssignRequest",
    "SegmentAssignResult",
    "SegmentBase",
    "SegmentCreate",
    "SegmentOut",
    "SegmentSummary",
    "SegmentUpdate",
    "SpendPointsRequest",
    "TierBase",
    "TierCreate",
    "TierOut",
    "TierUpdate",
]
