"""Tier domain logic.

``apply_tier`` is called from every path that changes a member's balance (points,
redemptions, challenge completion, member creation). It lived in the tiers
*router* before, which is why four routers imported each other.
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Member, Tier


def get_tier_or_404(db: Session, tier_id: UUID) -> Tier:
    tier = db.get(Tier, tier_id)
    if not tier:
        raise HTTPException(404, "Tier not found")
    return tier


def apply_tier(db: Session, member: Member) -> None:
    """Assign `member` to the highest tier whose min_points they meet."""
    tier = (
        db.query(Tier)
        .filter(Tier.min_points <= member.total_points)
        .order_by(Tier.min_points.desc())
        .first()
    )
    member.tier_id = tier.id if tier else None
