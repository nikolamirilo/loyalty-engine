"""Challenge domain logic: expiry, segment fan-out, progress and completion rewards."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import InvalidInput, NotFound
from app.models import (
    Challenge,
    ChallengeAssignment,
    ChallengeSegmentAssignment,
    ChallengeStatus,
    Member,
    MemberSegment,
    Program,
    Reward,
    TransactionType,
)
from app.schemas import ChallengeProgressOut
from app.services.points import record_transaction
from app.services.rewards import grant_prize, is_available


def now() -> datetime:
    return datetime.now(timezone.utc)


def is_expired(challenge: Challenge) -> bool:
    if challenge.expires_at is None:
        return False
    # expires_at read from the DB may be naive; treat stored values as UTC.
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < now()


def compute_assignment_expiry(
    challenge: Challenge, assigned_at: datetime
) -> Optional[datetime]:
    """The personal deadline for a member assigned to `challenge` at `assigned_at`.

    Prefers the challenge's relative `expiry_days` (resolved to a concrete
    timestamp so a later edit to `expiry_days` doesn't retroactively shift
    deadlines already handed out), falling back to its absolute `expires_at`
    so challenges without `expiry_days` keep today's shared-deadline behavior.
    """
    if challenge.expiry_days is not None:
        return assigned_at + timedelta(days=challenge.expiry_days)
    return challenge.expires_at


def assignment_is_expired(assignment: ChallengeAssignment) -> bool:
    if assignment.expires_at is None:
        return False
    # expires_at read from the DB may be naive; treat stored values as UTC.
    expires_at = assignment.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < now()


def get_challenge_or_404(
    db: Session, challenge_id: UUID, program: Program, lock: bool = False
) -> Challenge:
    q = db.query(Challenge).filter(
        Challenge.id == challenge_id, Challenge.program_id == program.id
    )
    if lock:
        q = q.with_for_update()
    challenge = q.first()
    if not challenge:
        raise NotFound("Challenge not found")
    return challenge


def get_assignment_or_404(
    db: Session, member_id: UUID, challenge_id: UUID, lock: bool = False
) -> ChallengeAssignment:
    q = db.query(ChallengeAssignment).filter(
        ChallengeAssignment.member_id == member_id,
        ChallengeAssignment.challenge_id == challenge_id,
    )
    if lock:
        q = q.with_for_update()
    assignment = q.first()
    if not assignment:
        raise NotFound("Challenge is not assigned to this member")
    return assignment


def assert_joinable(challenge: Challenge) -> None:
    """Guard the shared preconditions for handing a challenge to anyone."""
    if not challenge.is_active:
        raise InvalidInput("Challenge is not active")
    if is_expired(challenge):
        raise InvalidInput("Challenge has expired")


def sync_assignments_for_segments(
    db: Session, program: Program, segment_ids: set[UUID], member_ids: set[UUID]
) -> None:
    """Assign any active, non-expired challenges bulk-assigned to `segment_ids`
    to each member in `member_ids`, skipping (member, challenge) pairs that
    already exist.

    Call this whenever a member's segment membership changes (joins a segment
    via creation, update, or bulk segment assignment) - assigning a challenge to
    a segment only pushes it to that segment's *current* members, so members who
    join afterwards would otherwise never get it.
    """
    if not segment_ids or not member_ids:
        return

    challenge_ids = {
        challenge_id
        for (challenge_id,) in db.query(ChallengeSegmentAssignment.challenge_id)
        .filter(ChallengeSegmentAssignment.segment_id.in_(segment_ids))
        .distinct()
        .all()
    }
    if not challenge_ids:
        return

    challenges_by_id = {
        c.id: c
        for c in db.query(Challenge)
        .filter(Challenge.id.in_(challenge_ids), Challenge.program_id == program.id)
        .all()
        if c.is_active and not is_expired(c)
    }
    eligible_challenge_ids = set(challenges_by_id)
    if not eligible_challenge_ids:
        return

    existing = {
        (member_id, challenge_id)
        for member_id, challenge_id in db.query(
            ChallengeAssignment.member_id, ChallengeAssignment.challenge_id
        )
        .filter(
            ChallengeAssignment.member_id.in_(member_ids),
            ChallengeAssignment.challenge_id.in_(eligible_challenge_ids),
        )
        .all()
    }

    for member_id in member_ids:
        for challenge_id in eligible_challenge_ids:
            if (member_id, challenge_id) not in existing:
                assigned_at = now()
                db.add(
                    ChallengeAssignment(
                        member_id=member_id,
                        challenge_id=challenge_id,
                        assigned_at=assigned_at,
                        expires_at=compute_assignment_expiry(challenges_by_id[challenge_id], assigned_at),
                    )
                )


def assign_to_segment(
    db: Session, program: Program, challenge: Challenge, segment_id: UUID
) -> tuple[int, int]:
    """Hand `challenge` to every member of `segment_id` who doesn't have it yet.

    Returns ``(assigned, skipped)``. Check `assert_joinable` first. The caller
    commits.
    """
    # Members already holding this challenge - skip them.
    already = {
        member_id
        for (member_id,) in db.query(ChallengeAssignment.member_id)
        .filter(ChallengeAssignment.challenge_id == challenge.id)
        .all()
    }

    member_ids = {
        member_id
        for (member_id,) in db.query(MemberSegment.member_id)
        .join(MemberSegment.member)
        .filter(MemberSegment.segment_id == segment_id, Member.program_id == program.id)
        .all()
    }

    assigned = 0
    skipped = 0
    for member_id in member_ids:
        if member_id in already:
            skipped += 1
            continue
        assigned_at = now()
        db.add(
            ChallengeAssignment(
                member_id=member_id,
                challenge_id=challenge.id,
                assigned_at=assigned_at,
                expires_at=compute_assignment_expiry(challenge, assigned_at),
            )
        )
        assigned += 1

    # Remember the segment this challenge was pushed to (only when it actually
    # matched members, so an empty segment doesn't get recorded). Idempotent
    # thanks to the uq_challenge_segment constraint + this pre-check.
    if assigned + skipped > 0:
        already_recorded = (
            db.query(ChallengeSegmentAssignment.id)
            .filter(
                ChallengeSegmentAssignment.challenge_id == challenge.id,
                ChallengeSegmentAssignment.segment_id == segment_id,
            )
            .first()
        )
        if not already_recorded:
            db.add(ChallengeSegmentAssignment(challenge_id=challenge.id, segment_id=segment_id))

    return assigned, skipped


def new_assignment(member_id: UUID, challenge: Challenge) -> ChallengeAssignment:
    """A fresh assignment of `challenge`, with the member's own deadline worked
    out from now. Check `assert_joinable` first; the caller adds and commits."""
    assigned_at = now()
    return ChallengeAssignment(
        member_id=member_id,
        challenge=challenge,
        assigned_at=assigned_at,
        expires_at=compute_assignment_expiry(challenge, assigned_at),
    )


def progress_blocker(assignment: ChallengeAssignment) -> Optional[str]:
    """Why `assignment` can't take progress right now, or None if it can.

    An assignment found past its deadline is marked expired here, so the
    progress endpoint and event rules leave it in the same state. The caller
    commits.
    """
    if assignment.status in (ChallengeStatus.completed, ChallengeStatus.cancelled):
        return f"Challenge is already {assignment.status.value}"
    if assignment_is_expired(assignment):
        assignment.status = ChallengeStatus.expired
        return "Challenge has expired"
    return None


def member_progress(db: Session, challenge: Challenge, member_id: UUID) -> ChallengeProgressOut:
    """Challenge info + this member's progress on it, combined into one response.

    Works whether or not the member has been assigned the challenge yet
    (`is_assigned` covers that). Once assigned, `expires_at`/`is_expired`/
    `effective_status` describe the member's personal deadline
    (`assignment.expires_at`, resolved from the challenge's `expiry_days` or
    absolute `expires_at` at assignment time) rather than the challenge's own
    campaign window - and are recomputed here rather than trusted from the
    assignment's stored `status`, since that field is only updated lazily by
    the write paths (assign/progress) and can lag past the actual deadline.
    Before assignment there's no personal deadline yet, so this falls back to
    the challenge's absolute `expires_at`, which is what gates joinability.
    """
    assignment = (
        db.query(ChallengeAssignment)
        .filter(
            ChallengeAssignment.member_id == member_id,
            ChallengeAssignment.challenge_id == challenge.id,
        )
        .first()
    )

    if assignment:
        expired = assignment_is_expired(assignment)
        effective_expires_at = assignment.expires_at
    else:
        expired = is_expired(challenge)
        effective_expires_at = challenge.expires_at
    current_value = assignment.current_value if assignment else 0
    effective_status = assignment.status if assignment else None
    if assignment and expired and effective_status not in (ChallengeStatus.completed, ChallengeStatus.cancelled):
        effective_status = ChallengeStatus.expired

    return ChallengeProgressOut(
        id=challenge.id,
        name=challenge.name,
        description=challenge.description,
        target_value=challenge.target_value,
        reward_points=challenge.reward_points,
        reward_id=challenge.reward_id,
        is_active=challenge.is_active,
        starts_at=challenge.starts_at,
        expires_at=effective_expires_at,
        is_assigned=assignment is not None,
        assignment_id=assignment.id if assignment else None,
        current_value=current_value,
        progress_percent=min(100, round(current_value / challenge.target_value * 100)),
        remaining=max(challenge.target_value - current_value, 0),
        is_expired=expired,
        effective_status=effective_status,
        assigned_at=assignment.assigned_at if assignment else None,
        completed_at=assignment.completed_at if assignment else None,
    )


def force_complete(db: Session, assignment: ChallengeAssignment) -> None:
    """Admin force-complete: grants the rewards regardless of progress or
    deadline, but never twice and never for a cancelled assignment. The
    caller commits.
    """
    if assignment.status == ChallengeStatus.completed:
        raise InvalidInput("Challenge is already completed")
    if assignment.status == ChallengeStatus.cancelled:
        raise InvalidInput("Challenge is cancelled")
    complete_assignment(db, assignment)


def apply_progress(db: Session, assignment: ChallengeAssignment, amount: int) -> None:
    """Add `amount` progress, completing the challenge (and paying out its
    rewards) once it reaches the target. Check `progress_blocker` first. The
    caller commits.
    """
    assignment.current_value += amount
    if assignment.current_value >= assignment.challenge.target_value:
        complete_assignment(db, assignment)
    else:
        assignment.status = ChallengeStatus.in_progress


def complete_assignment(db: Session, assignment: ChallengeAssignment) -> None:
    """Mark an assignment completed and grant its challenge's rewards.

    Awards the challenge's fixed ``reward_points`` (earn transaction + tier
    re-apply) and/or assigns the linked reward as a prize (redemption with
    ``source=assigned``). Granting the prize is best-effort: if the reward is
    missing, inactive or out of stock the challenge still completes. The caller
    commits.
    """
    challenge = assignment.challenge
    # Lock the member row: this branch mutates total_points, and the
    # assignment's own row lock (see callers) doesn't cover the related
    # member row. Without this, a concurrent points earn/burn/adjust/redeem
    # (or another challenge completing for the same member) can race and
    # silently lose one of the two updates.
    member = db.query(Member).filter(Member.id == assignment.member_id).with_for_update().first()
    assert member is not None, "assignment.member_id must reference an existing member"

    assignment.status = ChallengeStatus.completed
    assignment.completed_at = now()
    assignment.current_value = max(assignment.current_value, challenge.target_value)

    # Points reward - fixed grant (no tier multiplier; that is for activity points).
    if challenge.reward_points > 0:
        record_transaction(
            db,
            member,
            challenge.reward_points,
            TransactionType.earn,
            f"Challenge completed: {challenge.name}",
        )

    # Prize reward - best effort, so an unavailable reward doesn't block completion.
    if challenge.reward_id is not None:
        reward = (
            db.query(Reward)
            .filter(
                Reward.id == challenge.reward_id,
                Reward.program_id == challenge.program_id,
            )
            .with_for_update()
            .first()
        )
        if reward is not None and is_available(reward):
            grant_prize(db, member.id, reward)
