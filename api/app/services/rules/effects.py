"""Rule effects: what a matching rule does to the member.

One handler per effect type, each with two jobs:

- ``validate`` runs when a rule is saved. It checks what the schema can't,
  such as the reward existing in this program, and returns the JSON to store.
- ``apply`` runs for each matching event. It never raises for a missing or
  unavailable target: it returns a skipped outcome instead, so one stale
  effect can't block the rest of the event.

Handlers only call the existing domain services, so points, prizes, challenge
progress and segments follow the same rules as their own endpoints. Adding an
effect means one schema class, one handler, and one entry in ``HANDLERS``.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.models import (
    Challenge,
    ChallengeAssignment,
    EventRule,
    EventType,
    Member,
    MemberSegment,
    Program,
    Reward,
    Segment,
    TransactionType,
)
from app.schemas import (
    AddChallengeProgressEffect,
    AddPointsEffect,
    AddToSegmentEffect,
    AssignChallengeEffect,
    BurnPointsEffect,
    GrantRewardEffect,
    RemoveFromSegmentEffect,
    RuleEffect,
    UpdateMemberEffect,
)
from app.services.challenges import (
    apply_progress,
    assert_joinable,
    get_challenge_or_404,
    new_assignment,
    progress_blocker,
    sync_assignments_for_segments,
)
from app.services.points import record_transaction
from app.services.rewards import get_reward_or_404, grant_prize, is_available
from app.services.rules.fields import (
    CUSTOM_PREFIX,
    EVENT_PREFIX,
    coerce_value,
    event_fields,
    writable_fields,
)
from app.services.segments import get_segment_or_404


@dataclass
class EffectContext:
    db: Session
    program: Program
    member: Member  # locked for the whole event
    event_type: EventType
    attributes: Dict[str, Any]
    rule: EventRule
    # The member's tier multiplier when the event arrived. Taken up front so a
    # tier change from an earlier effect can't change what a later one earns.
    multiplier: float


@dataclass
class Outcome:
    summary: str
    skipped: bool = False
    points: Optional[int] = None
    reward_id: Optional[UUID] = None


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


class EffectHandler:
    def validate(self, db: Session, program: Program, event_type: EventType, effect: Any) -> Dict[str, Any]:
        return effect.model_dump(mode="json", by_alias=True)

    def apply(self, ctx: EffectContext, effect: Any) -> Outcome:
        raise NotImplementedError


def _check_amount_source(event_type: EventType, fixed: Optional[int], from_attribute: Optional[str], what: str) -> None:
    """An effect's number is fixed or read from a number attribute, not both."""
    if fixed is not None and from_attribute is not None:
        raise HTTPException(400, f"Set {what} to a fixed number or to an event attribute, not both.")
    if from_attribute is not None:
        spec = event_fields(event_type).get(EVENT_PREFIX + from_attribute)
        if spec is None or spec.type != "number":
            raise HTTPException(400, f"{what.capitalize()} can only come from a number attribute of this event.")


def _read_amount(ctx: EffectContext, fixed: Optional[int], from_attribute: Optional[str]) -> Optional[float]:
    """The fixed number, or what the event sent for `from_attribute` (None if nothing)."""
    return ctx.attributes.get(from_attribute) if from_attribute is not None else fixed


def _check_points(event_type: EventType, effect: Any) -> None:
    if effect.points is None and effect.from_attribute is None:
        raise HTTPException(400, "Set points to a fixed number or to an event attribute.")
    _check_amount_source(event_type, effect.points, effect.from_attribute, "points")


def _ledger_note(ctx: EffectContext) -> str:
    return f"Effect of event {ctx.event_type.name}"


class AddPoints(EffectHandler):
    """Earn a fixed number of points, or as many as a number attribute says.
    The tier multiplier applies, the same as a manual earn."""

    def validate(self, db, program, event_type, effect: AddPointsEffect):
        _check_points(event_type, effect)
        return super().validate(db, program, event_type, effect)

    def apply(self, ctx, effect: AddPointsEffect):
        base = _read_amount(ctx, effect.points, effect.from_attribute)
        if base is None:
            return Outcome(f"No points: the event had no {effect.from_attribute}", skipped=True)
        awarded = round(base * ctx.multiplier)
        if awarded <= 0:
            return Outcome("No points to earn", skipped=True)
        record_transaction(ctx.db, ctx.member, awarded, TransactionType.earn, _ledger_note(ctx))
        return Outcome(f"Earned {_plural(awarded, 'point')}", points=awarded)


class BurnPoints(EffectHandler):
    """Spend a fixed number of points, or as many as a number attribute says.
    Like a manual burn, it never takes the balance below zero: a member without
    enough points is skipped. The tier multiplier doesn't apply."""

    def validate(self, db, program, event_type, effect: BurnPointsEffect):
        _check_points(event_type, effect)
        return super().validate(db, program, event_type, effect)

    def apply(self, ctx, effect: BurnPointsEffect):
        base = _read_amount(ctx, effect.points, effect.from_attribute)
        if base is None:
            return Outcome(f"No points burned: the event had no {effect.from_attribute}", skipped=True)
        burned = round(base)
        if burned <= 0:
            return Outcome("No points to burn", skipped=True)
        if ctx.member.total_points < burned:
            return Outcome(
                f"Not enough points to burn {burned}: the member has {ctx.member.total_points}", skipped=True
            )
        record_transaction(ctx.db, ctx.member, -burned, TransactionType.spend, _ledger_note(ctx))
        return Outcome(f"Burned {_plural(burned, 'point')}", points=-burned)


class GrantReward(EffectHandler):
    """Hand over a reward for free, if it is active and in stock."""

    def validate(self, db, program, event_type, effect: GrantRewardEffect):
        get_reward_or_404(db, effect.reward_id, program)
        return super().validate(db, program, event_type, effect)

    def apply(self, ctx, effect: GrantRewardEffect):
        reward = (
            ctx.db.query(Reward)
            .filter(Reward.id == effect.reward_id, Reward.program_id == ctx.program.id)
            .with_for_update()
            .first()
        )
        if reward is None:
            return Outcome("Reward no longer exists", skipped=True)
        if not is_available(reward):
            return Outcome(f'"{reward.name}" is inactive or out of stock', skipped=True)
        grant_prize(ctx.db, ctx.member.id, reward)
        return Outcome(f'Gave reward "{reward.name}"', reward_id=reward.id)


class AssignChallenge(EffectHandler):
    """Start a challenge for the member, as the member page's Assign does.
    Members who already have it, in any state, are skipped."""

    def validate(self, db, program, event_type, effect: AssignChallengeEffect):
        get_challenge_or_404(db, effect.challenge_id, program)
        return super().validate(db, program, event_type, effect)

    def apply(self, ctx, effect: AssignChallengeEffect):
        challenge = (
            ctx.db.query(Challenge)
            .filter(Challenge.id == effect.challenge_id, Challenge.program_id == ctx.program.id)
            .first()
        )
        if challenge is None:
            return Outcome("Challenge no longer exists", skipped=True)
        try:
            assert_joinable(challenge)
        except HTTPException as exc:
            return Outcome(f'"{challenge.name}": {str(exc.detail).lower()}', skipped=True)
        has_it = (
            ctx.db.query(ChallengeAssignment.id)
            .filter(
                ChallengeAssignment.member_id == ctx.member.id,
                ChallengeAssignment.challenge_id == challenge.id,
            )
            .first()
        )
        if has_it is not None:
            return Outcome(f'Already has the challenge "{challenge.name}"', skipped=True)
        ctx.db.add(new_assignment(ctx.member.id, challenge))
        # The session doesn't autoflush: flush so a later effect of this event,
        # such as challenge progress, finds the new assignment.
        ctx.db.flush()
        return Outcome(f'Assigned challenge "{challenge.name}"')


class AddChallengeProgress(EffectHandler):
    """Move a challenge the member already has. Members without it are skipped."""

    def validate(self, db, program, event_type, effect: AddChallengeProgressEffect):
        _check_amount_source(event_type, effect.amount, effect.from_attribute, "progress")
        get_challenge_or_404(db, effect.challenge_id, program)
        stored = super().validate(db, program, event_type, effect)
        if effect.amount is None and effect.from_attribute is None:
            stored["amount"] = 1
        return stored

    def apply(self, ctx, effect: AddChallengeProgressEffect):
        challenge = (
            ctx.db.query(Challenge)
            .filter(Challenge.id == effect.challenge_id, Challenge.program_id == ctx.program.id)
            .first()
        )
        if challenge is None:
            return Outcome("Challenge no longer exists", skipped=True)
        raw = _read_amount(ctx, effect.amount if effect.amount is not None else 1, effect.from_attribute)
        if raw is None:
            return Outcome(f"No progress: the event had no {effect.from_attribute}", skipped=True)
        amount = round(raw)
        if amount <= 0:
            return Outcome("No progress to add", skipped=True)
        assignment = (
            ctx.db.query(ChallengeAssignment)
            .filter(
                ChallengeAssignment.member_id == ctx.member.id,
                ChallengeAssignment.challenge_id == challenge.id,
            )
            .with_for_update()
            .first()
        )
        if assignment is None:
            return Outcome(f'Doesn\'t have the challenge "{challenge.name}"', skipped=True)
        reason = progress_blocker(assignment)
        if reason:
            return Outcome(f'"{challenge.name}": {reason.lower()}', skipped=True)
        apply_progress(ctx.db, assignment, amount)
        if assignment.completed_at is not None:
            return Outcome(f'Completed "{challenge.name}"')
        return Outcome(f'Added {amount} progress to "{challenge.name}"')


class AddToSegment(EffectHandler):
    """Put the member in a segment, which also hands them its challenges."""

    def validate(self, db, program, event_type, effect: AddToSegmentEffect):
        get_segment_or_404(db, effect.segment_id, program)
        return super().validate(db, program, event_type, effect)

    def apply(self, ctx, effect: AddToSegmentEffect):
        segment = (
            ctx.db.query(Segment)
            .filter(Segment.id == effect.segment_id, Segment.program_id == ctx.program.id)
            .first()
        )
        if segment is None:
            return Outcome("Segment no longer exists", skipped=True)
        if any(sa.segment_id == segment.id for sa in ctx.member.segment_assignments):
            return Outcome(f'Already in "{segment.name}"', skipped=True)
        ctx.member.segment_assignments.append(MemberSegment(segment_id=segment.id))
        sync_assignments_for_segments(ctx.db, ctx.program, {segment.id}, {ctx.member.id})
        return Outcome(f'Added to segment "{segment.name}"')


class RemoveFromSegment(EffectHandler):
    """Take the member out of a segment. Challenges it handed them are kept."""

    def validate(self, db, program, event_type, effect: RemoveFromSegmentEffect):
        get_segment_or_404(db, effect.segment_id, program)
        return super().validate(db, program, event_type, effect)

    def apply(self, ctx, effect: RemoveFromSegmentEffect):
        segment = (
            ctx.db.query(Segment)
            .filter(Segment.id == effect.segment_id, Segment.program_id == ctx.program.id)
            .first()
        )
        if segment is None:
            return Outcome("Segment no longer exists", skipped=True)
        link = next((sa for sa in ctx.member.segment_assignments if sa.segment_id == segment.id), None)
        if link is None:
            return Outcome(f'Not in "{segment.name}"', skipped=True)
        ctx.member.segment_assignments.remove(link)
        return Outcome(f'Removed from segment "{segment.name}"')


def _display(value: Any) -> str:
    if value is None:
        return "empty"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


class UpdateMember(EffectHandler):
    """Set one or more member fields, each to a fixed value or to a copy of an
    event attribute. Values are type-checked like any member attribute write."""

    def validate(self, db, program, event_type, effect: UpdateMemberEffect):
        writable = writable_fields(db, program)
        sources = event_fields(event_type)
        seen: set[str] = set()
        stored = []
        for update in effect.fields:
            spec = writable.get(update.field)
            if spec is None:
                raise HTTPException(400, f"'{update.field}' can't be updated by a rule.")
            if update.field in seen:
                raise HTTPException(400, f"'{spec.label}' is set twice in one effect.")
            seen.add(update.field)

            if update.from_attribute is not None:
                if update.value is not None:
                    raise HTTPException(400, f"Set '{spec.label}' from a value or from an attribute, not both.")
                source = sources.get(EVENT_PREFIX + update.from_attribute)
                if source is None:
                    raise HTTPException(400, f"This event has no attribute '{update.from_attribute}'.")
                # Anything reads as text; otherwise the types have to agree.
                if spec.type not in ("text", source.type):
                    raise HTTPException(
                        400, f"'{source.label}' ({source.type}) can't be copied into '{spec.label}' ({spec.type})."
                    )
                stored.append({"field": update.field, "value": None, "fromAttribute": update.from_attribute})
                continue

            value = coerce_value(spec, update.value)
            if update.field == "member.name" and not value:
                raise HTTPException(400, "A member's name can't be set to empty.")
            stored.append({"field": update.field, "value": value, "fromAttribute": None})
        return {"type": effect.type, "fields": stored}

    def apply(self, ctx, effect: UpdateMemberEffect):
        writable = writable_fields(ctx.db, ctx.program)
        identity = ctx.member.identity
        custom = dict(ctx.member.custom_attributes or {})
        changed: List[str] = []
        problems: List[str] = []

        for update in effect.fields:
            spec = writable.get(update.field)
            if spec is None:
                problems.append(f"{update.field} no longer exists")
                continue
            raw = ctx.attributes.get(update.from_attribute) if update.from_attribute else update.value
            if update.from_attribute and raw is None:
                problems.append(f"the event had no {update.from_attribute}")
                continue
            try:
                value = coerce_value(spec, raw)
            except HTTPException as exc:
                problems.append(str(exc.detail))
                continue

            if update.field == "member.name":
                if not value:
                    problems.append("name can't be empty")
                    continue
                identity.name = value
            elif update.field == "member.phone":
                identity.phone = value
            else:
                custom[update.field[len(CUSTOM_PREFIX):]] = value
            changed.append(f"{spec.label.lower()} to {_display(value)}")

        # Reassign rather than mutate: plain JSONB isn't change-tracked.
        if custom != (ctx.member.custom_attributes or {}):
            ctx.member.custom_attributes = custom

        if not changed:
            return Outcome("Nothing updated: " + "; ".join(problems), skipped=True)
        summary = "Set " + ", ".join(changed)
        if problems:
            summary += " (skipped: " + "; ".join(problems) + ")"
        return Outcome(summary)


HANDLERS: Dict[str, EffectHandler] = {
    "addPoints": AddPoints(),
    "burnPoints": BurnPoints(),
    "grantReward": GrantReward(),
    "assignChallenge": AssignChallenge(),
    "addChallengeProgress": AddChallengeProgress(),
    "addToSegment": AddToSegment(),
    "removeFromSegment": RemoveFromSegment(),
    "updateMember": UpdateMember(),
}

_EFFECT = TypeAdapter(RuleEffect)


def validate_effects(
    db: Session, program: Program, event_type: EventType, effects: List[BaseModel]
) -> List[Dict[str, Any]]:
    return [HANDLERS[e.type].validate(db, program, event_type, e) for e in effects]


def apply_effect(ctx: EffectContext, stored: Dict[str, Any]) -> Outcome:
    try:
        effect = _EFFECT.validate_python(stored)
    except ValidationError:
        return Outcome("This effect is no longer valid. Edit the rule to fix it.", skipped=True)
    return HANDLERS[effect.type].apply(ctx, effect)
