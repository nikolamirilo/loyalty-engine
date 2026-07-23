from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Member, MemberSegment, Segment, Tier
from routers.tiers import apply_tier
from schemas import MemberCreate, MemberUpdate, MemberOut

router = APIRouter(prefix="/members", tags=["Members"])

_SEGMENTS_OPT = selectinload(Member.segment_assignments).selectinload(MemberSegment.segment)


def _sync_member_segments(db: Session, member: Member, segment_ids: list[UUID]) -> None:
    """Replace `member`'s segment memberships with exactly `segment_ids`."""
    unique_ids = set(segment_ids)
    if unique_ids:
        found = {s.id for s in db.query(Segment.id).filter(Segment.id.in_(unique_ids)).all()}
        missing = unique_ids - found
        if missing:
            raise HTTPException(404, f"Segment(s) not found: {', '.join(str(i) for i in missing)}")
    member.segment_assignments = [MemberSegment(segment_id=sid) for sid in unique_ids]


@router.post("", response_model=MemberOut, status_code=201)
def create_member(body: MemberCreate, db: Session = Depends(get_db)):
    if db.query(Member).filter(Member.email == body.email).first():
        raise HTTPException(400, "Email already registered")
    data = body.model_dump(exclude={"segment_ids"})
    member = Member(**data)
    db.add(member)
    db.flush()
    _sync_member_segments(db, member, body.segment_ids)
    apply_tier(db, member)
    db.commit()
    db.refresh(member)
    return member


def _members_query(db: Session, q: Optional[str]):
    query = db.query(Member)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(Member.name.ilike(pattern), Member.email.ilike(pattern))
        )
    return query


@router.get("", response_model=list[MemberOut])
def list_members(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # Stable ordering is required for correct offset/limit pagination.
    return (
        _members_query(db, q)
        .options(_SEGMENTS_OPT)
        .order_by(Member.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/count")
def count_members(q: Optional[str] = None, db: Session = Depends(get_db)):
    # Declared before /{member_id} so "count" isn't parsed as a member id.
    total = _members_query(db, q).with_entities(func.count(Member.id)).scalar()
    return {"count": total or 0}


@router.get("/stats")
def member_stats(db: Session = Depends(get_db)):
    """Dashboard aggregates computed server-side so the client doesn't download
    every member just to tally them: total count, points in circulation, and the
    member-count-per-tier distribution.

    Tiers are bucketed by balance (the highest tier whose ``min_points`` the
    balance meets), matching the client's ``tierForBalance`` rule."""
    tiers = db.query(Tier).order_by(Tier.min_points.asc()).all()

    count = 0
    points_in_circulation = 0
    by_tier: dict[str, int] = {}
    untiered = 0

    # Scan only the balance column (compact) rather than whole member rows.
    for (total_points,) in db.query(Member.total_points).all():
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
def get_member(member_id: UUID, db: Session = Depends(get_db)):
    member = (
        db.query(Member).options(_SEGMENTS_OPT).filter(Member.id == member_id).first()
    )
    if not member:
        raise HTTPException(404, "Member not found")
    return member


@router.patch("/{member_id}", response_model=MemberOut)
def update_member(member_id: UUID, body: MemberUpdate, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    data = body.model_dump(exclude_none=True, exclude={"segment_ids"})
    for field, value in data.items():
        setattr(member, field, value)
    if body.segment_ids is not None:
        _sync_member_segments(db, member, body.segment_ids)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: UUID, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    db.delete(member)
    db.commit()
