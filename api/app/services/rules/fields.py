"""What a rule can read and write.

Paths mirror JSON callers already see: ``event.attributes.amount`` is the
``amount`` a caller sends in an event's ``attributes``, and
``member.customAttributes.store`` is the ``store`` in ``MemberOut``. Conditions
and effects both resolve their paths here, so they always agree on what exists.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models import EventType, Member, MemberAttribute, Program
from app.services.custom_attributes import coerce

EVENT_PREFIX = "event.attributes."
CUSTOM_PREFIX = "member.customAttributes."

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
