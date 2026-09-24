"""Challenge domain logic: expiry, segment fan-out, and completion rewards."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    Challenge,
    ChallengeAssignment,
    ChallengeSegmentAssignment,
    ChallengeStatus,
    Member,
    Program,
    Reward,
    TransactionType,
)
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
        raise HTTPException(404, "Challenge not found")
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
        raise HTTPException(404, "Challenge is not assigned to this member")
    return assignment


def assert_joinable(challenge: Challenge) -> None:
    """Guard the shared preconditions for handing a challenge to anyone."""
    if not challenge.is_active:
        raise HTTPException(400, "Challenge is not active")
    if is_expired(challenge):
        raise HTTPException(400, "Challenge has expired")


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
