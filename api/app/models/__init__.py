"""SQLAlchemy models.

Importing this package registers every mapped class on ``Base.metadata``, which
is what makes ``create_all`` and the string-based relationship targets resolve.
Import models from here (``from app.models import Member``) rather than from the
individual modules, so that registration is never partial.
"""

from app.models.challenge import (
    Challenge,
    ChallengeAssignment,
    ChallengeSegmentAssignment,
)
from app.models.email_verification import EmailVerificationCode
from app.models.enums import (
    ChallengeStatus,
    MemberAttributeType,
    RedemptionSource,
    TransactionType,
)
from app.models.member import Member, MemberSegment
from app.models.member_attribute import MemberAttribute
from app.models.points import PointsTransaction
from app.models.redemption import Redemption
from app.models.reward import Reward
from app.models.segment import Segment
from app.models.tier import Tier

__all__ = [
    "Challenge",
    "ChallengeAssignment",
    "ChallengeSegmentAssignment",
    "ChallengeStatus",
    "EmailVerificationCode",
    "Member",
    "MemberAttribute",
    "MemberAttributeType",
    "MemberSegment",
    "PointsTransaction",
    "Redemption",
    "RedemptionSource",
    "Reward",
    "Segment",
    "Tier",
    "TransactionType",
]
