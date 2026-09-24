from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.program import get_program
from app.models import Member, MemberSegment, Program, Segment
from app.schemas import (
    MemberAssignRequest,
    MemberAssignResult,
    SegmentCreate,
    SegmentOut,
    SegmentUpdate,
)
from app.services.challenges import sync_assignments_for_segments
from app.services.segments import get_segment_or_404
from app.services.tiers import reapply_tiers

router = APIRouter(prefix="/segments", tags=["Segments"])


@router.post("", response_model=SegmentOut, status_code=201)
def create_segment(
    body: SegmentCreate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    if (
        db.query(Segment)
        .filter(Segment.program_id == program.id, Segment.name == body.name)
        .first()
    ):
        raise HTTPException(400, "Segment name already exists")
    segment = Segment(**body.model_dump(), program_id=program.id)
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


@router.get("", response_model=list[SegmentOut])
def list_segments(
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    # selectinload the member assignments so serializing SegmentOut.member_count
    # doesn't lazy-load one query per segment (N+1).
    return (
        db.query(Segment)
        .filter(Segment.program_id == program.id)
        .options(selectinload(Segment.member_assignments))
        .order_by(Segment.name)
        .all()
    )


@router.get("/{segment_id}", response_model=SegmentOut)
def get_segment(
    segment_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return get_segment_or_404(db, segment_id, program)


@router.patch("/{segment_id}", response_model=SegmentOut)
def update_segment(
    segment_id: UUID,
    body: SegmentUpdate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    segment = get_segment_or_404(db, segment_id, program)
    data = body.model_dump(exclude_none=True)
    if "name" in data and data["name"] != segment.name:
        if (
            db.query(Segment)
            .filter(Segment.program_id == program.id, Segment.name == data["name"])
            .first()
        ):
            raise HTTPException(400, "Segment name already exists")
    for field, value in data.items():
        setattr(segment, field, value)
    db.commit()
    db.refresh(segment)
    return segment


@router.delete("/{segment_id}", status_code=204)
def delete_segment(
    segment_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    segment = get_segment_or_404(db, segment_id, program)
    db.delete(segment)
    db.commit()


@router.post("/{segment_id}/assign", response_model=MemberAssignResult)
def assign_segment_to_members(
    segment_id: UUID,
    body: MemberAssignRequest,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    get_segment_or_404(db, segment_id, program)

    member_ids = set(body.member_ids)
    if member_ids:
        # Scoped to the program, so a member id from another program reads as
        # missing rather than being pulled into this program's segment.
        found = {
            m
            for (m,) in db.query(Member.id)
            .filter(Member.id.in_(member_ids), Member.program_id == program.id)
            .all()
        }
        missing = member_ids - found
        if missing:
            raise HTTPException(404, f"Member(s) not found: {', '.join(str(i) for i in missing)}")

    already = {
        member_id
        for (member_id,) in db.query(MemberSegment.member_id)
        .filter(MemberSegment.segment_id == segment_id, MemberSegment.member_id.in_(member_ids))
        .all()
    }

    assigned = 0
    skipped = 0
    newly_assigned: set[UUID] = set()
    for member_id in member_ids:
        if member_id in already:
            skipped += 1
            continue
        db.add(MemberSegment(member_id=member_id, segment_id=segment_id))
        newly_assigned.add(member_id)
        assigned += 1

    # Covers both newly-assigned members and pre-existing ones, so it also
    # backfills any challenge that was bulk-assigned to this segment before
    # this endpoint carried the sync.
    sync_assignments_for_segments(db, program, {segment_id}, member_ids)

    if newly_assigned:
        # A tier's conditions can read segments; flush so each member's
        # `segment_assignments` reflects the rows just added above.
        db.flush()
        members = db.query(Member).filter(Member.id.in_(newly_assigned)).all()
        reapply_tiers(db, program.id, members)

    db.commit()
    return MemberAssignResult(segment_id=segment_id, assigned=assigned, skipped=skipped)
