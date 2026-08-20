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


class DOIType(str, enum.Enum):
    """How a DOI verification email asks the member to confirm their address.

    ``code``: the email shows a 6-digit code the member types back into
    whatever screen triggered the flow.
    ``link``: the email carries a link that verifies for the member - today
    that is the client's ``/verify`` page, where one button does it.

    Both name what the email carries, not where it lands: where the link goes
    is a client concern the API contract shouldn't pin down.
    """

    code = "code"
    link = "link"
