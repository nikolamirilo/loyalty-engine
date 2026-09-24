"""Tier domain logic.

A tier's conditions read the same field language as an event rule's ``if``
(``app.services.rules``): points balance, lifetime purchase spend and count,
segments, and custom attributes. All of a tier's conditions must hold - the
same "no OR, no nesting" rule an event rule's conditions follow - which is how
"spend at least €200 AND hold the VIP segment" is expressed as one tier.

Tiers are tried from the highest ``rank`` down (ties break by creation order),
and a member is assigned to the first whose conditions all match, or to none
if no tier's do.

``apply_tier`` (or its batched sibling ``reapply_tiers``) is called from every
path that changes a value a tier's conditions can read: points, purchases,
segment membership, custom attributes, and a tier definition itself.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Member, Tier
from app.services.products import get_purchase_totals_by_member


def _ordered_tiers(db: Session, program_id: UUID) -> List[Tier]:
    return (
        db.query(Tier)
        .filter(Tier.program_id == program_id)
        .order_by(Tier.rank.desc(), Tier.created_at.asc())
        .all()
    )


def _best_tier(tiers: List[Tier], context: Dict[str, Any]) -> Optional[Tier]:
    # Imported lazily: `app.services.rules` (via its `effects` module) reaches
    # back into `app.services.points` and `app.services.challenges`, both of
    # which import `apply_tier` from this module - a module-level import here
    # would be circular.
    from app.services.rules.conditions import matches

    return next((tier for tier in tiers if matches(tier.conditions, context)), None)


def _tier_context(db: Session, member: Member, purchase_totals: Optional[tuple[int, int]] = None) -> Dict[str, Any]:
    from app.services.rules.fields import build_tier_context

    return build_tier_context(db, member, purchase_totals)


def apply_tier(db: Session, member: Member) -> None:
    """Assign `member` to the highest-ranked tier whose conditions they meet.

    The program comes off the membership rather than being passed in, so
    every call site stays correct: a member belongs to exactly one program
    and can only ever hold a tier defined by it.
    """
    tiers = _ordered_tiers(db, member.program_id)
    tier = _best_tier(tiers, _tier_context(db, member)) if tiers else None
    member.tier_id = tier.id if tier else None


def reapply_tiers(db: Session, program_id: UUID, members: Optional[List[Member]] = None) -> None:
    """`apply_tier` for `members` (every member in the program, by default).

    Used where more than one member's tier can change at once: a tier's own
    definition changing (it affects the whole program), or a bulk action like
    assigning a segment to many members. Purchase totals are fetched once for
    the whole batch instead of once per member.
    """
    if members is None:
        members = db.query(Member).filter(Member.program_id == program_id).all()
    if not members:
        return
    tiers = _ordered_tiers(db, program_id)
    totals = get_purchase_totals_by_member(db, [m.id for m in members])
    for member in members:
        context = _tier_context(db, member, totals.get(member.id, (0, 0)))
        tier = _best_tier(tiers, context) if tiers else None
        member.tier_id = tier.id if tier else None
