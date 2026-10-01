from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.core.program import get_program
from app.models import (
    Challenge,
    ChallengeAssignment,
    ChallengeSegmentAssignment,
    ChallengeStatus,
    Member,
    Program,
    Reward,
    Segment,
)
from app.schemas import (
    ChallengeAssignmentOut,
    ChallengeCreate,
    ChallengeOut,
    ChallengeProgressOut,
    ChallengeUpdate,
    ProgressRequest,
    SegmentAssignRequest,
    SegmentAssignResult,
)
from app.services.challenges import (
    apply_progress,
    assert_joinable,
    assign_to_segment,
    force_complete,
    get_assignment_or_404,
    get_challenge_or_404,
    member_progress,
    new_assignment,
    progress_blocker,
)
from app.services.scoping import get_scoped_or_404

router = APIRouter(tags=["Challenges"])


# ── challenge definitions (backend/admin CRUD) ───────────────────────────────

@router.post("/challenges", response_model=ChallengeOut, status_code=201)
def create_challenge(
    body: ChallengeCreate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    if body.reward_id is not None:
        get_scoped_or_404(db, Reward, body.reward_id, program, "Reward")
    challenge = Challenge(**body.model_dump(), program_id=program.id)
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.get("/challenges", response_model=list[ChallengeOut])
def list_challenges(
    # Aliased so the wire-level query key is camelCase like every other JSON
    # key in the API; the Python parameter stays snake_case.
    active_only: bool = Query(False, alias="activeOnly"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    # selectinload the segment assignments (+ each one's segment) so serializing
    # ChallengeOut.segments doesn't lazy-load one query per challenge (N+1).
    q = (
        db.query(Challenge)
        .options(
            selectinload(Challenge.segment_assignments).selectinload(ChallengeSegmentAssignment.segment)
        )
        .filter(Challenge.program_id == program.id)
    )
    if active_only:
        q = q.filter(Challenge.is_active)
    return q.order_by(Challenge.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/challenges/{challenge_id}", response_model=ChallengeOut)
def get_challenge(
    challenge_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return get_challenge_or_404(db, challenge_id, program)


@router.patch("/challenges/{challenge_id}", response_model=ChallengeOut)
def update_challenge(
    challenge_id: UUID,
    body: ChallengeUpdate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    challenge = get_challenge_or_404(db, challenge_id, program)
    data = body.model_dump(exclude_unset=True)
    if data.get("reward_id") is not None:
        get_scoped_or_404(db, Reward, data["reward_id"], program, "Reward")
    for field, value in data.items():
        setattr(challenge, field, value)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.delete("/challenges/{challenge_id}", status_code=204)
def delete_challenge(
    challenge_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    challenge = get_challenge_or_404(db, challenge_id, program)
    db.delete(challenge)
    db.commit()


# ── assignment & progress (member-centric) ───────────────────────────────────

@router.post("/members/{member_id}/challenges/{challenge_id}", response_model=ChallengeAssignmentOut, status_code=201)
def assign_challenge(
    member_id: UUID,
    challenge_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    get_scoped_or_404(db, Member, member_id, program, "Member")
    challenge = get_challenge_or_404(db, challenge_id, program)
    assert_joinable(challenge)

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

    assignment = new_assignment(member_id, challenge)
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
    program: Program = Depends(get_program),
):
    # Resolving the member inside the program scopes the assignments below:
    # they hang off the membership, so they cannot belong to another program.
    get_scoped_or_404(db, Member, member_id, program, "Member")
    # joinedload the challenge so serializing ChallengeAssignmentOut.challenge
    # doesn't lazy-load one query per row (N+1); selectinload its segments (+
    # each one's segment) so the nested ChallengeOut.segments doesn't add
    # another query per row.
    q = (
        db.query(ChallengeAssignment)
        .options(
            joinedload(ChallengeAssignment.challenge)
            .selectinload(Challenge.segment_assignments)
            .selectinload(ChallengeSegmentAssignment.segment)
        )
        .filter(ChallengeAssignment.member_id == member_id)
    )
    if status is not None:
        q = q.filter(ChallengeAssignment.status == status)
    return q.order_by(ChallengeAssignment.assigned_at.desc()).offset(skip).limit(limit).all()


@router.get("/members/{member_id}/challenges/{challenge_id}", response_model=ChallengeProgressOut)
def get_member_challenge_progress(
    member_id: UUID,
    challenge_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Challenge info + this member's progress on it, combined into one response.

    Works whether or not the member has been assigned the challenge yet
    (`isAssigned` covers that). Once assigned, the deadline and status are the
    member's own; before that, they are the challenge's.
    """
    get_scoped_or_404(db, Member, member_id, program, "Member")
    challenge = get_challenge_or_404(db, challenge_id, program)
    return member_progress(db, challenge, member_id)


@router.post("/members/{member_id}/challenges/{challenge_id}/progress", response_model=ChallengeAssignmentOut)
def add_progress(
    member_id: UUID,
    challenge_id: UUID,
    body: ProgressRequest,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    # Resolve the membership inside the program first: the assignment is then
    # reachable only if it belongs to a member of this program.
    get_scoped_or_404(db, Member, member_id, program, "Member")
    assignment = get_assignment_or_404(db, member_id, challenge_id, lock=True)

    reason = progress_blocker(assignment)
    if reason:
        # Persists the expired status, if the check just found the deadline passed.
        db.commit()
        raise HTTPException(400, reason)

    apply_progress(db, assignment, body.amount)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.post("/members/{member_id}/challenges/{challenge_id}/complete", response_model=ChallengeAssignmentOut)
def complete_challenge(
    member_id: UUID,
    challenge_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Admin force-complete - grants rewards regardless of progress or deadline."""
    get_scoped_or_404(db, Member, member_id, program, "Member")
    assignment = get_assignment_or_404(db, member_id, challenge_id, lock=True)
    force_complete(db, assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/members/{member_id}/challenges/{challenge_id}", status_code=204)
def unassign_challenge(
    member_id: UUID,
    challenge_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    get_scoped_or_404(db, Member, member_id, program, "Member")
    assignment = get_assignment_or_404(db, member_id, challenge_id)
    db.delete(assignment)
    db.commit()


# ── bulk assignment by segment ───────────────────────────────────────────────

@router.post("/challenges/{challenge_id}/assign-segment", response_model=SegmentAssignResult)
def assign_challenge_to_segment(
    challenge_id: UUID,
    body: SegmentAssignRequest,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    challenge = get_challenge_or_404(db, challenge_id, program)
    assert_joinable(challenge)
    get_scoped_or_404(db, Segment, body.segment_id, program, "Segment")
    assigned, skipped = assign_to_segment(db, program, challenge, body.segment_id)
    db.commit()
    return SegmentAssignResult(
        challenge_id=challenge_id,
        segment_id=body.segment_id,
        assigned=assigned,
        skipped=skipped,
    )
