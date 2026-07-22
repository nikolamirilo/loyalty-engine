from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from models import Member, Tier
from routers.tiers import apply_tier
from schemas import MemberCreate, MemberUpdate, MemberOut

router = APIRouter(prefix="/members", tags=["Members"])


@router.post("", response_model=MemberOut, status_code=201)
def create_member(body: MemberCreate, db: Session = Depends(get_db)):
    if db.query(Member).filter(Member.email == body.email).first():
        raise HTTPException(400, "Email already registered")
    member = Member(**body.model_dump())
    db.add(member)
    db.flush()
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
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    return member


@router.patch("/{member_id}", response_model=MemberOut)
def update_member(member_id: UUID, body: MemberUpdate, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(member, field, value)
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
