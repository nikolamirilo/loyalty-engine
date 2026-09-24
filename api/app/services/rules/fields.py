"""What a rule can read and write.

Paths mirror JSON callers already see: ``event.attributes.amount`` is the
``amount`` a caller sends in an event's ``attributes``, and
``member.customAttributes.store`` is the ``store`` in ``MemberOut``. Conditions
and effects both resolve their paths here, so they always agree on what exists.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import EventType, Member, MemberAttribute, Program
from app.services.custom_attributes import coerce
from app.services.products import get_purchase_totals

EVENT_PREFIX = "event.attributes."
CUSTOM_PREFIX = "member.customAttributes."

# Paths into a member's purchase history. Lifetime totals only - a tier
# doesn't re-evaluate on a schedule, only when something it can read changes,
# and a windowed figure (e.g. "spend in the last 30 days") would silently go
# stale between one triggering change and the next.
PURCHASE_SPEND = "member.purchaseSpendCents"
PURCHASE_COUNT = "member.purchaseCount"

# Field types beyond the member attribute types, for member values that
# reference another row.
TIER = "tier"
SEGMENTS = "segments"


@dataclass(frozen=True)
class FieldSpec:
    """A value a rule can reference.

    ``label``, ``type`` and ``options`` are exactly what
    ``custom_attributes.coerce`` reads, so a value can be checked against a
    spec the same way a member attribute value is.
    """

    path: str
    label: str
    type: str
    options: Optional[list[str]] = None


def coerce_value(spec: FieldSpec, raw: Any) -> Any:
    """``coerce`` plus one tidy-up: a whole number parsed from text stays an int."""
    value = coerce(spec, raw)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def event_fields(event_type: EventType) -> Dict[str, FieldSpec]:
    return {
        EVENT_PREFIX + a["key"]: FieldSpec(EVENT_PREFIX + a["key"], a["label"], a["type"], a.get("options"))
        for a in event_type.attributes
    }


def _custom_fields(db: Session, program: Program) -> Dict[str, FieldSpec]:
    return {
        CUSTOM_PREFIX + a.key: FieldSpec(CUSTOM_PREFIX + a.key, a.label, a.type, a.options)
        for a in db.query(MemberAttribute).filter(MemberAttribute.program_id == program.id).all()
    }


def readable_fields(db: Session, program: Program, event_type: EventType) -> Dict[str, FieldSpec]:
    """Everything a condition on ``event_type`` can test."""
    return {
        **event_fields(event_type),
        "member.pointsBalance": FieldSpec("member.pointsBalance", "Points balance", "number"),
        "member.tier": FieldSpec("member.tier", "Tier", TIER),
        "member.segments": FieldSpec("member.segments", "Segments", SEGMENTS),
        **_custom_fields(db, program),
    }


def writable_fields(db: Session, program: Program) -> Dict[str, FieldSpec]:
    """Everything an ``updateMember`` effect can set.

    Email is left out on purpose: it is unique across every program and tied
    to email verification, so it only changes through the member endpoints.
    Name and phone belong to the person, so a change shows in every program.
    """
    return {
        "member.name": FieldSpec("member.name", "Name", "text"),
        "member.phone": FieldSpec("member.phone", "Phone", "text"),
        **_custom_fields(db, program),
    }


def build_context(member: Member, attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Every readable value for one event, keyed by path.

    Taken once, before any effect runs, so every rule sees the member as they
    were when the event arrived and rule order never changes the outcome.
    """
    return {
        **{EVENT_PREFIX + k: v for k, v in attributes.items()},
        "member.pointsBalance": member.total_points,
        "member.tier": str(member.tier_id) if member.tier_id else None,
        "member.segments": [str(sa.segment_id) for sa in member.segment_assignments],
        **{CUSTOM_PREFIX + k: v for k, v in (member.custom_attributes or {}).items()},
    }


def tier_fields(db: Session, program: Program) -> Dict[str, FieldSpec]:
    """Everything a tier's conditions can test.

    Deliberately leaves out ``member.tier``: a tier can't be defined in terms
    of the tier it is itself deciding.
    """
    return {
        "member.pointsBalance": FieldSpec("member.pointsBalance", "Points balance", "number"),
        PURCHASE_SPEND: FieldSpec(PURCHASE_SPEND, "Lifetime purchase spend (cents)", "number"),
        PURCHASE_COUNT: FieldSpec(PURCHASE_COUNT, "Lifetime purchase count", "number"),
        "member.segments": FieldSpec("member.segments", "Segments", SEGMENTS),
        **_custom_fields(db, program),
    }


def build_tier_context(
    db: Session, member: Member, purchase_totals: Optional[Tuple[int, int]] = None
) -> Dict[str, Any]:
    """Every value a tier's conditions can test for `member`, keyed by path.

    `purchase_totals` is `(count, spend_cents)`; pass it when the caller
    already has totals for several members at once (see
    `app.services.products.get_purchase_totals_by_member`) so this doesn't
    issue one purchase query per member. Left out, it is fetched for just
    this one.
    """
    count, spend_cents = purchase_totals if purchase_totals is not None else get_purchase_totals(db, member.id)
    return {
        "member.pointsBalance": member.total_points,
        PURCHASE_SPEND: spend_cents,
        PURCHASE_COUNT: count,
        "member.segments": [str(sa.segment_id) for sa in member.segment_assignments],
        **{CUSTOM_PREFIX + k: v for k, v in (member.custom_attributes or {}).items()},
    }
