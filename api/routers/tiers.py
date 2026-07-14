from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Tier
from schemas import TierCreate, TierOut

router = APIRouter(prefix="/tiers", tags=["Tiers"])


@router.post("", response_model=TierOut, status_code=201)
def create_tier(body: TierCreate, db: Session = Depends(get_db)):
    if db.query(Tier).filter(Tier.name == body.name).first():
        raise HTTPException(400, "Tier name already exists")
    tier = Tier(**body.model_dump())
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@router.get("", response_model=list[TierOut])
def list_tiers(db: Session = Depends(get_db)):
    return db.query(Tier).order_by(Tier.min_points).all()


@router.get("/{tier_id}", response_model=TierOut)
def get_tier(tier_id: UUID, db: Session = Depends(get_db)):
    tier = db.get(Tier, tier_id)
    if not tier:
        raise HTTPException(404, "Tier not found")
    return tier


@router.delete("/{tier_id}", status_code=204)
def delete_tier(tier_id: UUID, db: Session = Depends(get_db)):
    tier = db.get(Tier, tier_id)
    if not tier:
        raise HTTPException(404, "Tier not found")
    db.delete(tier)
    db.commit()
