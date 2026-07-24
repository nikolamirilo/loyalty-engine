from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Member, MemberSegment, Segment
from schemas import (
    MemberAssignRequest,
    MemberAssignResult,
    SegmentCreate,
    SegmentOut,
    SegmentUpdate,
)

router = APIRouter(prefix="/segments", tags=["Segments"])


def _get_segment_or_404(db: Session, segment_id: UUID) -> Segment:
    segment = db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(404, "Segment not found")
    return segment


@router.post("", response_model=SegmentOut, status_code=201)
def create_segment(body: SegmentCreate, db: Session = Depends(get_db)):
    if db.query(Segment).filter(Segment.name == body.name).first():
        raise HTTPException(400, "Segment name already exists")
    segment = Segment(**body.model_dump())
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


@router.get("", response_model=list[SegmentOut])
def list_segments(db: Session = Depends(get_db)):
    # selectinload the member assignments so serializing SegmentOut.member_count
    # doesn't lazy-load one query per segment (N+1).
    return (
        db.query(Segment)
        .options(selectinload(Segment.member_assignments))
        .order_by(Segment.name)
        .all()
    )


@router.get("/{segment_id}", response_model=SegmentOut)
def get_segment(segment_id: UUID, db: Session = Depends(get_db)):
    return _get_segment_or_404(db, segment_id)


@router.patch("/{segment_id}", response_model=SegmentOut)
def update_segment(segment_id: UUID, body: SegmentUpdate, db: Session = Depends(get_db)):
    segment = _get_segment_or_404(db, segment_id)
    data = body.model_dump(exclude_none=True)
    if "name" in data and data["name"] != segment.name:
        if db.query(Segment).filter(Segment.name == data["name"]).first():
            raise HTTPException(400, "Segment name already exists")
    for field, value in data.items():
        setattr(segment, field, value)
    db.commit()
    db.refresh(segment)
    return segment


@router.delete("/{segment_id}", status_code=204)
def delete_segment(segment_id: UUID, db: Session = Depends(get_db)):
    segment = _get_segment_or_404(db, segment_id)
    db.delete(segment)
    db.commit()


@router.post("/{segment_id}/assign", response_model=MemberAssignResult)
def assign_segment_to_members(segment_id: UUID, body: MemberAssignRequest, db: Session = Depends(get_db)):
    _get_segment_or_404(db, segment_id)

    member_ids = set(body.member_ids)
    if member_ids:
        found = {m for (m,) in db.query(Member.id).filter(Member.id.in_(member_ids)).all()}
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
    for member_id in member_ids:
        if member_id in already:
            skipped += 1
            continue
        db.add(MemberSegment(member_id=member_id, segment_id=segment_id))
        assigned += 1

    db.commit()
    return MemberAssignResult(segment_id=segment_id, assigned=assigned, skipped=skipped)
