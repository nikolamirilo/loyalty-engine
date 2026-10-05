from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.core.program import get_program
from app.models import Member, MemberIdentity, MemberSegment, Program
from app.schemas import (
    MemberCountOut,
    MemberCreate,
    MemberOut,
    MemberProgramOut,
    MemberStatsOut,
    MemberUpdate,
)
from app.services.members import edit_member, register_member, remove_member, summarize_members
from app.services.memberships import join

router = APIRouter(prefix="/members", tags=["Members"])

_SEGMENTS_OPT = selectinload(Member.segment_assignments).selectinload(MemberSegment.segment)
# `MemberOut` serializes the member's tier, so eager-load it here too - without
# this, listing members lazy-loads one tier per row (a classic N+1).
_TIER_OPT = joinedload(Member.tier)

# The person's name and email live on the identity, and `MemberOut` reads them
# through `Member.name`/`Member.email`. Without this every listed member costs
# an extra query.
_IDENTITY_OPT = selectinload(Member.identity)


def _get_member_or_404(db: Session, member_id: UUID, program: Program) -> Member:
    member = (
        db.query(Member)
        .options(_SEGMENTS_OPT, _IDENTITY_OPT, _TIER_OPT)
        .filter(Member.id == member_id, Member.program_id == program.id)
        .first()
    )
    if not member:
        raise HTTPException(404, "Member not found")
    return member


@router.post("", response_model=MemberOut, status_code=201)
def create_member(
    body: MemberCreate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    member = register_member(db, program, body)
    db.commit()
    db.refresh(member)
    return member


def _members_query(db: Session, program: Program, q: Optional[str]):
    # Joined unconditionally: the person's name and email live on the identity,
    # so both the search filter and the serialized response need it.
    query = db.query(Member).join(Member.identity).filter(Member.program_id == program.id)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(MemberIdentity.name.ilike(pattern), MemberIdentity.email.ilike(pattern))
        )
    return query


@router.get("", response_model=list[MemberOut])
def list_members(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    # Stable ordering is required for correct offset/limit pagination.
    return (
        _members_query(db, program, q)
        .options(_SEGMENTS_OPT, _IDENTITY_OPT, _TIER_OPT)
        .order_by(Member.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/count", response_model=MemberCountOut)
def count_members(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    # Declared before /{member_id} so "count" isn't parsed as a member id.
    total = _members_query(db, program, q).with_entities(func.count(Member.id)).scalar()
    return {"count": total or 0}


@router.get("/stats", response_model=MemberStatsOut)
def member_stats(
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Total members, points in circulation and members per tier."""
    return summarize_members(db, program)


@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return _get_member_or_404(db, member_id, program)


@router.get("/{member_id}/programs", response_model=list[MemberProgramOut])
def list_member_programs(
    member_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Every program, marked with this person's membership in each.

    Deliberately spans programs: it answers "where else am I a member", which
    is what the member app's program switcher and the console's cross-program
    view are both asking. Only the person behind `member_id` is exposed, never
    another program's data.
    """
    member = _get_member_or_404(db, member_id, program)
    joined = {
        m.program_id: m.id
        for m in db.query(Member).filter(Member.identity_id == member.identity_id).all()
    }
    return [
        # Every ProgramOut field (branding included) straight off the row, so a
        # field added to programs later cannot be silently left out here.
        MemberProgramOut.model_validate(p).model_copy(update={"member_id": joined.get(p.id)})
        for p in db.query(Program).order_by(Program.created_at.asc()).all()
    ]


@router.post("/{member_id}/programs/{program_id}", response_model=MemberOut)
def join_program(
    member_id: UUID,
    program_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """This person's membership in `program_id`, joining them if it is new.

    Switching program is the one operation that has to reach across the
    boundary, so `program_id` is looked up unscoped on purpose. The caller is
    still proving who they are with a `member_id` inside the program the
    request addresses; all this returns is the same person's membership
    elsewhere, starting from zero points if they had none.
    """
    member = _get_member_or_404(db, member_id, program)
    target = db.get(Program, program_id)
    if not target:
        raise HTTPException(404, "Program not found")

    membership = join(db, target, member.identity)
    db.commit()
    db.refresh(membership)
    return membership


@router.patch("/{member_id}", response_model=MemberOut)
def update_member(
    member_id: UUID,
    body: MemberUpdate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    member = _get_member_or_404(db, member_id, program)
    edit_member(db, program, member, body)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
def delete_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Delete the member from every program.

    Members are global, so this removes the person and all of their
    memberships, after which their email address is free to register again.
    """
    member = _get_member_or_404(db, member_id, program)
    remove_member(db, member)
    db.commit()
