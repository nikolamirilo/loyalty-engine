from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.program import get_program
from app.models import Member, MemberIdentity, MemberSegment, Program, Segment, Tier
from app.schemas import (
    MemberCountOut,
    MemberCreate,
    MemberOut,
    MemberProgramOut,
    MemberStatsOut,
    MemberUpdate,
)
from app.services.challenges import sync_assignments_for_segments
from app.services.custom_attributes import defaults_for_new_member, validate_payload
from app.services.memberships import join
from app.services.tiers import apply_tier

router = APIRouter(prefix="/members", tags=["Members"])

_SEGMENTS_OPT = selectinload(Member.segment_assignments).selectinload(MemberSegment.segment)
# The person's name and email live on the identity, and `MemberOut` reads them
# through `Member.name`/`Member.email`. Without this every listed member costs
# an extra query.
_IDENTITY_OPT = selectinload(Member.identity)

# Fields of `MemberUpdate` that belong to the person rather than to this
# membership, so a write lands on the identity and is visible in every program
# that person has joined.
PERSON_FIELDS = frozenset({"name", "email", "phone"})


def _sync_member_segments(
    db: Session, member: Member, program: Program, segment_ids: list[UUID]
) -> None:
    """Replace `member`'s segment memberships with exactly `segment_ids`.

    Diffs against the current assignments instead of recreating the whole
    collection: callers (e.g. the member edit form) resend the full segment
    list on every save, even when it hasn't changed, and a wholesale replace
    would insert new rows for unchanged segments before deleting the old ones,
    tripping the `uq_member_segment` unique constraint against itself.
    """
    unique_ids = set(segment_ids)
    if unique_ids:
        found = {
            s.id
            for s in db.query(Segment.id)
            .filter(Segment.id.in_(unique_ids), Segment.program_id == program.id)
            .all()
        }
        missing = unique_ids - found
        if missing:
            raise HTTPException(404, f"Segment(s) not found: {', '.join(str(i) for i in missing)}")
    current = {sa.segment_id: sa for sa in member.segment_assignments}
    for segment_id, assignment in current.items():
        if segment_id not in unique_ids:
            member.segment_assignments.remove(assignment)
    for segment_id in unique_ids - current.keys():
        member.segment_assignments.append(MemberSegment(segment_id=segment_id))


def _get_member_or_404(db: Session, member_id: UUID, program: Program) -> Member:
    member = (
        db.query(Member)
        .options(_SEGMENTS_OPT, _IDENTITY_OPT)
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
    identity = db.query(MemberIdentity).filter(MemberIdentity.email == body.email).first()
    if identity is None:
        identity = MemberIdentity(name=body.name, email=body.email, phone=body.phone)
        db.add(identity)
        db.flush()
    else:
        # The person already exists, so this is an enrolment into a second
        # program rather than a new account. Their name and phone are left as
        # they are: joining a program is not a request to rename someone
        # everywhere else.
        already_joined = (
            db.query(Member)
            .filter(Member.identity_id == identity.id, Member.program_id == program.id)
            .first()
        )
        if already_joined:
            raise HTTPException(400, "This member has already joined this program")

    # Definition defaults fill in only the attributes the caller didn't supply, so
    # a member created through the API lands with the same values an admin sees
    # prefilled in the console's create form.
    custom = {
        **defaults_for_new_member(db, program.id),
        **validate_payload(db, program.id, body.custom_attributes),
    }
    member = Member(program_id=program.id, identity_id=identity.id, custom_attributes=custom)
    db.add(member)
    db.flush()
    _sync_member_segments(db, member, program, body.segment_ids)
    sync_assignments_for_segments(db, program, set(body.segment_ids), {member.id})
    apply_tier(db, member)
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
        .options(_SEGMENTS_OPT, _IDENTITY_OPT)
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
    """Dashboard aggregates computed server-side so the client doesn't download
    every member just to tally them: total count, points in circulation, and the
    member-count-per-tier distribution.

    Tiers are bucketed by balance (the highest tier whose ``min_points`` the
    balance meets), matching the client's ``tierForBalance`` rule."""
    tiers = (
        db.query(Tier)
        .filter(Tier.program_id == program.id)
        .order_by(Tier.min_points.asc())
        .all()
    )

    count = 0
    points_in_circulation = 0
    by_tier: dict[str, int] = {}
    untiered = 0

    # Scan only the balance column (compact) rather than whole member rows.
    for (total_points,) in (
        db.query(Member.total_points).filter(Member.program_id == program.id).all()
    ):
        balance = total_points or 0
        count += 1
        points_in_circulation += balance

        assigned = None
        for tier in tiers:  # ascending by min_points
            if balance >= tier.min_points:
                assigned = tier
            else:
                break
        if assigned is not None:
            key = str(assigned.id)
            by_tier[key] = by_tier.get(key, 0) + 1
        else:
            untiered += 1

    return {
        "count": count,
        "points_in_circulation": points_in_circulation,
        "by_tier": by_tier,
        "untiered": untiered,
    }


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
        MemberProgramOut(
            id=p.id,
            name=p.name,
            slug=p.slug,
            description=p.description,
            is_default=p.is_default,
            created_at=p.created_at,
            member_id=joined.get(p.id),
        )
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
    if body.email is not None and body.email != member.email:
        if (
            db.query(MemberIdentity)
            .filter(
                MemberIdentity.email == body.email,
                MemberIdentity.id != member.identity_id,
            )
            .first()
        ):
            raise HTTPException(400, "Email already registered")
    data = body.model_dump(
        exclude_none=True, exclude={"segment_ids", "custom_attributes", "email_verified"}
    )
    for field, value in data.items():
        setattr(member.identity if field in PERSON_FIELDS else member, field, value)
    if body.email_verified is not None:
        member.identity.email_verified_at = (
            datetime.now(timezone.utc) if body.email_verified else None
        )
    if body.custom_attributes is not None:
        # Shallow merge, not replace: a caller that knows about one attribute must
        # not wipe the others. A key sent as null clears just that value.
        # Reassignment (not in-place mutation) is what makes SQLAlchemy see the
        # change on a plain JSONB column.
        patch = validate_payload(db, program.id, body.custom_attributes)
        member.custom_attributes = {**(member.custom_attributes or {}), **patch}
    if body.segment_ids is not None:
        _sync_member_segments(db, member, program, body.segment_ids)
        sync_assignments_for_segments(db, program, set(body.segment_ids), {member_id})
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
def delete_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Remove the member from this program.

    Deletes the membership and everything hanging off it. The identity
    survives, so the person keeps their memberships in other programs and
    their email address stays registered.
    """
    member = _get_member_or_404(db, member_id, program)
    db.delete(member)
    db.commit()
