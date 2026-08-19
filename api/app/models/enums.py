"""Domain enums.

Kept free of any SQLAlchemy or ORM imports so schema modules can depend on them
without pulling in the mapped classes.
"""

import enum


class TransactionType(str, enum.Enum):
    earn = "earn"
    spend = "spend"
    adjust = "adjust"


class RedemptionSource(str, enum.Enum):
    redeemed = "redeemed"
    assigned = "assigned"


class ChallengeStatus(str, enum.Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    expired = "expired"
    cancelled = "cancelled"


class MemberAttributeType(str, enum.Enum):
    text = "text"
    number = "number"
    boolean = "boolean"
    date = "date"
    select = "select"
