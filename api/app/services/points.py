"""Points ledger logic.

Every balance change goes through ``record_transaction`` so the ledger row, the
denormalized ``total_points`` and the member's tier can never drift apart. The
caller commits.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import Member, PointsTransaction, TransactionType
from app.services.tiers import apply_tier


def record_transaction(
    db: Session,
    member: Member,
    points: int,
    tx_type: TransactionType,
    description: Optional[str] = None,
) -> PointsTransaction:
    """Append a ledger entry, move the balance by `points`, and re-apply the tier.

    `points` is signed: positive to credit, negative to debit. Callers are
    responsible for locking the member row and for validating that the resulting
    balance is acceptable.
    """
    tx = PointsTransaction(
        member_id=member.id,
        points=points,
        type=tx_type,
        description=description,
    )
    db.add(tx)
    member.total_points += points
    apply_tier(db, member)
    return tx
