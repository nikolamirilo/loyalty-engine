from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Member, Tier
from schemas import MemberCreate, MemberUpdate, MemberOut

router = APIRouter(prefix="/members", tags=["Members"])


def _assign_tier(db: Session, member: Member) -> None:
    tier = (
        db.query(Tier)
        .filter(Tier.min_points <= member.total_points)
        .order_by(Tier.min_points.desc())
        .first()
    )
    member.tier_id = tier.id if tier else None


@router.post("", response_model=MemberOut, status_code=201)
def create_member(body: MemberCreate, db: Session = Depends(get_db)):
    if db.query(Member).filter(Member.email == body.email).first():
        raise HTTPException(400, "Email already registered")
    member = Member(**body.model_dump())
    db.add(member)
    db.flush()
    _assign_tier(db, member)
    db.commit()
    db.refresh(member)
    return member


@router.get("", response_model=list[MemberOut])
def list_members(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Member).offset(skip).limit(limit).all()


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
