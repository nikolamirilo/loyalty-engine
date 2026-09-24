from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.program import get_program
from app.models import EventRule, EventType, Program
from app.schemas import (
    EventRuleCreate,
    EventRuleOut,
    EventRuleUpdate,
    EventTypeCreate,
    EventTypeOut,
    EventTypeUpdate,
)
from app.services.custom_attributes import slugify
from app.services.events import assert_attributes_unused, build_attributes
from app.services.rules import validate_rule
from app.services.rules.conditions import validate_conditions
from app.services.rules.effects import validate_effects
from app.services.rules.fields import readable_fields
from app.services.scoping import get_scoped_or_404

router = APIRouter(prefix="/event-types", tags=["Events"])


def _get_event_type_or_404(db: Session, event_type_id: UUID, program: Program) -> EventType:
    return get_scoped_or_404(db, EventType, event_type_id, program, "Event type")


def _get_rule_or_404(db: Session, event_type: EventType, rule_id: UUID) -> EventRule:
    rule = (
        db.query(EventRule)
        .filter(EventRule.id == rule_id, EventRule.event_type_id == event_type.id)
        .first()
    )
    if rule is None:
        raise HTTPException(404, "Rule not found")
    return rule


def _optional_text(value: str | None) -> str | None:
    return (value or "").strip() or None


# ── event types ──────────────────────────────────────────────────────────────


@router.post("", response_model=EventTypeOut, status_code=201)
def create_event_type(
    body: EventTypeCreate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    key = slugify(body.name)
    if db.query(EventType).filter(EventType.program_id == program.id, EventType.key == key).first():
        raise HTTPException(400, f"An event with the key '{key}' already exists")

    event_type = EventType(
        program_id=program.id,
        key=key,
        name=body.name.strip(),
        description=_optional_text(body.description),
        is_active=body.is_active,
        attributes=build_attributes(body.attributes, []),
    )
    db.add(event_type)
    db.commit()
    db.refresh(event_type)
    return event_type


@router.get("", response_model=list[EventTypeOut])
def list_event_types(
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return (
        db.query(EventType)
        .options(selectinload(EventType.rules))
        .filter(EventType.program_id == program.id)
        .order_by(EventType.created_at)
        .all()
    )


@router.get("/{event_type_id}", response_model=EventTypeOut)
def get_event_type(
    event_type_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return _get_event_type_or_404(db, event_type_id, program)


@router.patch("/{event_type_id}", response_model=EventTypeOut)
def update_event_type(
    event_type_id: UUID,
    body: EventTypeUpdate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    event_type = _get_event_type_or_404(db, event_type_id, program)
    sent = body.model_fields_set

    if body.name is not None:
        event_type.name = body.name.strip()
    if "description" in sent:
        event_type.description = _optional_text(body.description)
    if body.is_active is not None:
        event_type.is_active = body.is_active
    if body.attributes is not None:
        attributes = build_attributes(body.attributes, event_type.attributes)
        assert_attributes_unused(event_type, {a["key"] for a in attributes})
        event_type.attributes = attributes

    db.commit()
    db.refresh(event_type)
    return event_type


@router.delete("/{event_type_id}", status_code=204)
def delete_event_type(
    event_type_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Delete the event type and its rules. Events already received stay in
    each member's history, under the type's key."""
    event_type = _get_event_type_or_404(db, event_type_id, program)
    db.delete(event_type)
    db.commit()


# ── rules ────────────────────────────────────────────────────────────────────


@router.get("/{event_type_id}/rules", response_model=list[EventRuleOut])
def list_rules(
    event_type_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return _get_event_type_or_404(db, event_type_id, program).rules


@router.post("/{event_type_id}/rules", response_model=EventRuleOut, status_code=201)
def create_rule(
    event_type_id: UUID,
    body: EventRuleCreate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    event_type = _get_event_type_or_404(db, event_type_id, program)
    conditions, effects = validate_rule(db, program, event_type, body.conditions, body.effects)
    rule = EventRule(
        event_type_id=event_type.id,
        name=body.name.strip(),
        is_active=body.is_active,
        conditions=conditions,
        effects=effects,
        limit_per_member=body.limit_per_member,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{event_type_id}/rules/{rule_id}", response_model=EventRuleOut)
def update_rule(
    event_type_id: UUID,
    rule_id: UUID,
    body: EventRuleUpdate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    event_type = _get_event_type_or_404(db, event_type_id, program)
    rule = _get_rule_or_404(db, event_type, rule_id)
    sent = body.model_fields_set

    if body.name is not None:
        rule.name = body.name.strip()
    if body.is_active is not None:
        rule.is_active = body.is_active
    if body.conditions is not None:
        rule.conditions = validate_conditions(
            db, program, readable_fields(db, program, event_type), body.conditions
        )
    if body.effects is not None:
        rule.effects = validate_effects(db, program, event_type, body.effects)
    if "limit_per_member" in sent:
        rule.limit_per_member = body.limit_per_member

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{event_type_id}/rules/{rule_id}", status_code=204)
def delete_rule(
    event_type_id: UUID,
    rule_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    event_type = _get_event_type_or_404(db, event_type_id, program)
    db.delete(_get_rule_or_404(db, event_type, rule_id))
    db.commit()
