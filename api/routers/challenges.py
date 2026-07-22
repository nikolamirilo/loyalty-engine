from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from database import get_db
from models import (
    Challenge,
    ChallengeAssignment,
    ChallengeSegmentAssignment,
    ChallengeStatus,
    Member,
    PointsTransaction,
    Redemption,
    RedemptionSource,
    Reward,
    TransactionType,
)
from routers.tiers import apply_tier
from schemas import (
    ChallengeAssignmentOut,
    ChallengeCreate,
    ChallengeOut,
    ChallengeProgressOut,
    ChallengeUpdate,
    ProgressRequest,
    SegmentAssignRequest,
    SegmentAssignResult,
)

router = APIRouter(tags=["Challenges"])


# ── helpers ─────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(challenge: Challenge) -> bool:
    if challenge.expires_at is None:
        return False
    # expires_at read from the DB may be naive; treat stored values as UTC.
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < _now()


def _get_challenge_or_404(db: Session, challenge_id: UUID, lock: bool = False) -> Challenge:
    q = db.query(Challenge).filter(Challenge.id == challenge_id)
    if lock:
        q = q.with_for_update()
    challenge = q.first()
    if not challenge:
        raise HTTPException(404, "Challenge not found")
    return challenge


def _get_assignment_or_404(db: Session, member_id: UUID, challenge_id: UUID, lock: bool = False) -> ChallengeAssignment:
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


def _complete(db: Session, assignment: ChallengeAssignment) -> None:
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
    assignment.completed_at = _now()
    assignment.current_value = max(assignment.current_value, challenge.target_value)

    # Points reward - fixed grant (no tier multiplier; that is for activity points).
    if challenge.reward_points > 0:
        db.add(
            PointsTransaction(
                member_id=member.id,
                points=challenge.reward_points,
                type=TransactionType.earn,
                description=f"Challenge completed: {challenge.name}",
            )
        )
        member.total_points += challenge.reward_points
        apply_tier(db, member)

    # Prize reward - mirror assign_prize in routers/redemptions.py.
    if challenge.reward_id is not None:
        reward = db.query(Reward).filter(Reward.id == challenge.reward_id).with_for_update().first()
        if reward is not None and reward.is_active and not (reward.stock is not None and reward.stock <= 0):
            if reward.stock is not None:
                reward.stock -= 1
            db.add(
                Redemption(
                    member_id=member.id,
                    reward_id=reward.id,
                    points_spent=0,
                    source=RedemptionSource.assigned,
                )
            )


# ── challenge definitions (backend/admin CRUD) ───────────────────────────────

@router.post("/challenges", response_model=ChallengeOut, status_code=201)
def create_challenge(body: ChallengeCreate, db: Session = Depends(get_db)):
    if body.reward_id is not None and not db.get(Reward, body.reward_id):
        raise HTTPException(404, "Reward not found")
    challenge = Challenge(**body.model_dump())
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.get("/challenges", response_model=list[ChallengeOut])
def list_challenges(active_only: bool = False, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # selectinload the segment assignments so serializing ChallengeOut.segments
    # doesn't lazy-load one query per challenge (N+1).
    q = db.query(Challenge).options(selectinload(Challenge.segment_assignments))
    if active_only:
        q = q.filter(Challenge.is_active)
    return q.order_by(Challenge.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/challenges/{challenge_id}", response_model=ChallengeOut)
def get_challenge(challenge_id: UUID, db: Session = Depends(get_db)):
    return _get_challenge_or_404(db, challenge_id)


@router.patch("/challenges/{challenge_id}", response_model=ChallengeOut)
def update_challenge(challenge_id: UUID, body: ChallengeUpdate, db: Session = Depends(get_db)):
    challenge = _get_challenge_or_404(db, challenge_id)
    data = body.model_dump(exclude_unset=True)
    if data.get("reward_id") is not None and not db.get(Reward, data["reward_id"]):
        raise HTTPException(404, "Reward not found")
    for field, value in data.items():
        setattr(challenge, field, value)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.delete("/challenges/{challenge_id}", status_code=204)
def delete_challenge(challenge_id: UUID, db: Session = Depends(get_db)):
    challenge = _get_challenge_or_404(db, challenge_id)
    db.delete(challenge)
    db.commit()


# ── assignment & progress (member-centric) ───────────────────────────────────

@router.post("/members/{member_id}/challenges/{challenge_id}", response_model=ChallengeAssignmentOut, status_code=201)
def assign_challenge(member_id: UUID, challenge_id: UUID, db: Session = Depends(get_db)):
    if not db.get(Member, member_id):
        raise HTTPException(404, "Member not found")
    challenge = _get_challenge_or_404(db, challenge_id)
    if not challenge.is_active:
        raise HTTPException(400, "Challenge is not active")
    if _is_expired(challenge):
        raise HTTPException(400, "Challenge has expired")

    existing = (
        db.query(ChallengeAssignment)
        .filter(
            ChallengeAssignment.member_id == member_id,
            ChallengeAssignment.challenge_id == challenge_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Challenge already assigned to this member")

    assignment = ChallengeAssignment(member_id=member_id, challenge_id=challenge_id)
    db.add(assignment)
    try:
        db.commit()
    except IntegrityError:
        # Concurrent request won the race between the existence check above
        # and this insert; the uq_challenge_member constraint caught it.
        db.rollback()
        raise HTTPException(400, "Challenge already assigned to this member")
    db.refresh(assignment)
    return assignment


@router.get("/members/{member_id}/challenges", response_model=list[ChallengeAssignmentOut])
def list_member_challenges(
    member_id: UUID,
    status: Optional[ChallengeStatus] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    if not db.get(Member, member_id):
        raise HTTPException(404, "Member not found")
    # joinedload the challenge so serializing ChallengeAssignmentOut.challenge
    # doesn't lazy-load one query per row (N+1); selectinload its segments so
    # the nested ChallengeOut.segments doesn't add another query per row.
    q = (
        db.query(ChallengeAssignment)
        .options(
            joinedload(ChallengeAssignment.challenge).selectinload(
                Challenge.segment_assignments
            )
        )
        .filter(ChallengeAssignment.member_id == member_id)
    )
    if status is not None:
        q = q.filter(ChallengeAssignment.status == status)
    return q.order_by(ChallengeAssignment.assigned_at.desc()).offset(skip).limit(limit).all()


@router.get("/members/{member_id}/challenges/{challenge_id}", response_model=ChallengeProgressOut)
def get_member_challenge_progress(member_id: UUID, challenge_id: UUID, db: Session = Depends(get_db)):
    """Challenge info + this member's progress on it, combined into one response.

    Works whether or not the member has been assigned the challenge yet
    (`is_assigned` covers that). `is_expired`/`effective_status` are recomputed
    from `expires_at` rather than trusted from the assignment's stored `status`,
    since that field is only updated lazily by the write paths (assign/progress)
    and can lag past the actual deadline.
    """
    if not db.get(Member, member_id):
        raise HTTPException(404, "Member not found")
    challenge = _get_challenge_or_404(db, challenge_id)

    assignment = (
        db.query(ChallengeAssignment)
        .filter(
            ChallengeAssignment.member_id == member_id,
            ChallengeAssignment.challenge_id == challenge_id,
        )
        .first()
    )

    expired = _is_expired(challenge)
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
        expires_at=challenge.expires_at,
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


@router.post("/members/{member_id}/challenges/{challenge_id}/progress", response_model=ChallengeAssignmentOut)
def add_progress(member_id: UUID, challenge_id: UUID, body: ProgressRequest, db: Session = Depends(get_db)):
    assignment = _get_assignment_or_404(db, member_id, challenge_id, lock=True)

    if assignment.status in (ChallengeStatus.completed, ChallengeStatus.cancelled):
        raise HTTPException(400, f"Challenge is already {assignment.status.value}")

    challenge = assignment.challenge
    if assignment.status == ChallengeStatus.expired or _is_expired(challenge):
        if assignment.status != ChallengeStatus.expired:
            assignment.status = ChallengeStatus.expired
            db.commit()
        raise HTTPException(400, "Challenge has expired")

    assignment.current_value += body.amount
    if assignment.current_value >= challenge.target_value:
        _complete(db, assignment)
    else:
        assignment.status = ChallengeStatus.in_progress

    db.commit()
    db.refresh(assignment)
    return assignment


@router.post("/members/{member_id}/challenges/{challenge_id}/complete", response_model=ChallengeAssignmentOut)
def complete_challenge(member_id: UUID, challenge_id: UUID, db: Session = Depends(get_db)):
    """Admin force-complete - grants rewards regardless of progress or deadline."""
    assignment = _get_assignment_or_404(db, member_id, challenge_id, lock=True)
    if assignment.status == ChallengeStatus.completed:
        raise HTTPException(400, "Challenge is already completed")
    if assignment.status == ChallengeStatus.cancelled:
        raise HTTPException(400, "Challenge is cancelled")
    _complete(db, assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/members/{member_id}/challenges/{challenge_id}", status_code=204)
def unassign_challenge(member_id: UUID, challenge_id: UUID, db: Session = Depends(get_db)):
    assignment = _get_assignment_or_404(db, member_id, challenge_id)
    db.delete(assignment)
    db.commit()


# ── bulk assignment by segment ───────────────────────────────────────────────

@router.post("/challenges/{challenge_id}/assign-segment", response_model=SegmentAssignResult)
def assign_challenge_to_segment(challenge_id: UUID, body: SegmentAssignRequest, db: Session = Depends(get_db)):
    challenge = _get_challenge_or_404(db, challenge_id)
    if not challenge.is_active:
        raise HTTPException(400, "Challenge is not active")
    if _is_expired(challenge):
        raise HTTPException(400, "Challenge has expired")

    # Members already holding this challenge - skip them.
    already = {
        member_id
        for (member_id,) in db.query(ChallengeAssignment.member_id)
        .filter(ChallengeAssignment.challenge_id == challenge_id)
        .all()
    }

    # segments is a JSON (not JSONB) column, so filter candidates in Python.
    assigned = 0
    skipped = 0
    for member in db.query(Member).all():
        if body.segment not in (member.segments or []):
            continue
        if member.id in already:
            skipped += 1
            continue
        db.add(ChallengeAssignment(member_id=member.id, challenge_id=challenge_id))
        assigned += 1

    # Remember the segment this challenge was pushed to (only when it actually
    # matched members, so typos / empty segments don't get recorded). Idempotent
    # thanks to the uq_challenge_segment constraint + this pre-check.
    if assigned + skipped > 0:
        already_recorded = (
            db.query(ChallengeSegmentAssignment.id)
            .filter(
                ChallengeSegmentAssignment.challenge_id == challenge_id,
                ChallengeSegmentAssignment.segment == body.segment,
            )
            .first()
        )
        if not already_recorded:
            db.add(ChallengeSegmentAssignment(challenge_id=challenge_id, segment=body.segment))

    db.commit()
    return SegmentAssignResult(
        challenge_id=challenge_id,
        segment=body.segment,
        assigned=assigned,
        skipped=skipped,
    )
