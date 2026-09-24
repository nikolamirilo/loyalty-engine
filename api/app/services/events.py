"""Event types and received events.

``track_event`` is the rule engine's entry point: it records the event, runs
every active rule whose conditions match, and stores what each effect did,
all in one transaction.
"""

from typing import Any, Dict, List, Set, Tuple

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import EventRule, EventRuleRun, EventType, Member, MemberEvent, Program
from app.schemas import EventAttributeIn, TrackEventRequest
from app.services.custom_attributes import normalize_options, slugify
from app.services.rules.conditions import matches
from app.services.rules.effects import EffectContext, apply_effect
from app.services.rules.fields import EVENT_PREFIX, build_context, coerce_value, event_fields
from app.services.tiers import apply_tier

# ── event type attributes ────────────────────────────────────────────────────


def build_attributes(items: List[EventAttributeIn], existing: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Turn the attribute list from a create or update into what is stored.

    An item with a ``key`` keeps that existing attribute, whose type can't
    change: stored events and rules depend on it. An item without one is new,
    and gets a key derived from its label.
    """
    current = {a["key"]: a for a in existing}
    out = []
    for item in items:
        if item.key is not None:
            old = current.get(item.key)
            if old is None:
                raise HTTPException(400, f"Unknown attribute '{item.key}'. Leave the key out to add a new one.")
            if item.type.value != old["type"]:
                raise HTTPException(400, f"The type of '{old['label']}' can't change once created.")
            key = item.key
        else:
            key = slugify(item.label)
        out.append(
            {
                "key": key,
                "label": item.label.strip(),
                "type": item.type.value,
                "options": normalize_options(item.type.value, item.options),
            }
        )
    keys = [a["key"] for a in out]
    duplicates = sorted({k for k in keys if keys.count(k) > 1})
    if duplicates:
        raise HTTPException(400, f"Two attributes share the key '{duplicates[0]}'. Rename one of them.")
    return out


def _attributes_used_by(rule: EventRule) -> Set[str]:
    used = {
        c["field"][len(EVENT_PREFIX):] for c in rule.conditions if c["field"].startswith(EVENT_PREFIX)
    }
    for effect in rule.effects:
        if effect.get("fromAttribute"):
            used.add(effect["fromAttribute"])
        for update in effect.get("fields") or []:
            if update.get("fromAttribute"):
                used.add(update["fromAttribute"])
    return used


def assert_attributes_unused(event_type: EventType, kept: Set[str]) -> None:
    """Refuse to drop an attribute a rule still reads, which would leave the
    rule silently never matching."""
    labels = {a["key"]: a["label"] for a in event_type.attributes}
    removed = set(labels) - kept
    for rule in event_type.rules:
        in_use = sorted(removed & _attributes_used_by(rule))
        if in_use:
            raise HTTPException(
                400, f"'{labels[in_use[0]]}' is used by the rule '{rule.name}'. Change or delete that rule first."
            )


def validate_event_attributes(event_type: EventType, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce an incoming event's attributes against its definition.

    Unknown keys are rejected, so a typo in an integration shows up at once.
    Every attribute is optional: a condition on a missing one just doesn't match.
    """
    specs = event_fields(event_type)
    unknown = sorted(k for k in payload if EVENT_PREFIX + k not in specs)
    if unknown:
        raise HTTPException(400, f"Unknown attribute(s) for '{event_type.key}': {', '.join(unknown)}")
    return {k: coerce_value(specs[EVENT_PREFIX + k], v) for k, v in payload.items()}


# ── receiving events ─────────────────────────────────────────────────────────


def _runs_so_far(db: Session, rule: EventRule, member: Member) -> int:
    return (
        db.query(func.count(EventRuleRun.id))
        .filter(EventRuleRun.rule_id == rule.id, EventRuleRun.member_id == member.id)
        .scalar()
        or 0
    )


def _run_rules(
    db: Session, program: Program, member: Member, event_type: EventType, event: MemberEvent
) -> List[Dict[str, Any]]:
    context = build_context(member, event.attributes)
    multiplier = member.tier.multiplier if member.tier else 1.0
    applied: List[Dict[str, Any]] = []

    for rule in event_type.rules:
        if not rule.is_active or not matches(rule.conditions, context):
            continue
        if rule.limit_per_member is not None and _runs_so_far(db, rule, member) >= rule.limit_per_member:
            continue
        db.add(EventRuleRun(rule_id=rule.id, member_id=member.id, member_event_id=event.id))

        ctx = EffectContext(db, program, member, event_type, event.attributes, rule, multiplier)
        for stored in rule.effects:
            outcome = apply_effect(ctx, stored)
            applied.append(
                {
                    "ruleId": str(rule.id),
                    "ruleName": rule.name,
                    "type": stored.get("type"),
                    "summary": outcome.summary,
                    "skipped": outcome.skipped,
                    "points": outcome.points,
                    "rewardId": str(outcome.reward_id) if outcome.reward_id else None,
                }
            )

    # A tier's conditions can read segments and custom attributes as well as
    # points, and an addToSegment/removeFromSegment/updateMember effect above
    # doesn't re-apply the tier itself (addPoints/burnPoints already do, via
    # `record_transaction`). One re-check per event, after every effect has
    # run, covers all of them.
    if applied:
        apply_tier(db, member)
    return applied


def track_event(db: Session, program: Program, body: TrackEventRequest) -> Tuple[MemberEvent, bool]:
    """Record an event for a member and run its rules. Returns the stored
    event and whether it is new: an ``eventId`` already seen for this member
    returns the original event and runs nothing. Commits.
    """
    # Locked for the whole event: effects move the balance, and two events for
    # one member must not interleave. It also makes the eventId check below
    # safe against a concurrent retry of the same event.
    member = (
        db.query(Member)
        .filter(Member.id == body.member_id, Member.program_id == program.id)
        .with_for_update()
        .first()
    )
    if member is None:
        raise HTTPException(404, "Member not found")

    if body.event_id is not None:
        seen = (
            db.query(MemberEvent)
            .filter(MemberEvent.member_id == member.id, MemberEvent.external_id == body.event_id)
            .first()
        )
        if seen is not None:
            return seen, False

    event_type = (
        db.query(EventType)
        .filter(EventType.program_id == program.id, EventType.key == body.type)
        .first()
    )
    if event_type is None:
        raise HTTPException(400, f"Unknown event type '{body.type}'. Define it in the console first.")
    if not event_type.is_active:
        raise HTTPException(400, f"The event type '{body.type}' is inactive.")

    event = MemberEvent(
        member_id=member.id,
        event_type_id=event_type.id,
        type=event_type.key,
        attributes=validate_event_attributes(event_type, body.attributes),
        external_id=body.event_id,
    )
    db.add(event)
    db.flush()  # the rule runs below point at the event's id

    event.effects = _run_rules(db, program, member, event_type, event)
    db.commit()
    db.refresh(event)
    return event, True
