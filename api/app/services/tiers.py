"""Tier domain logic.

``apply_tier`` is called from every path that changes a member's balance (points,
redemptions, challenge completion, member creation). It lived in the tiers
*router* before, which is why four routers imported each other.
"""

from sqlalchemy.orm import Session

from app.models import Member, Tier


def apply_tier(db: Session, member: Member) -> None:
    """Assign `member` to the highest tier whose min_points they meet.

    The program comes off the membership rather than being passed in, so
    every call site stays correct: a member belongs to exactly one program
    and can only ever hold a tier defined by it.
    """
    tier = (
        db.query(Tier)
        .filter(
            Tier.program_id == member.program_id,
            Tier.min_points <= member.total_points,
        )
        .order_by(Tier.min_points.desc())
        .first()
    )
    member.tier_id = tier.id if tier else None
