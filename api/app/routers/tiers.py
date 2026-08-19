from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Tier
from app.schemas import TierCreate, TierOut, TierUpdate
from app.services.tiers import get_tier_or_404

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
    return get_tier_or_404(db, tier_id)


@router.patch("/{tier_id}", response_model=TierOut)
def update_tier(tier_id: UUID, body: TierUpdate, db: Session = Depends(get_db)):
    tier = get_tier_or_404(db, tier_id)
    data = body.model_dump(exclude_none=True)
    if "name" in data and data["name"] != tier.name:
        if db.query(Tier).filter(Tier.name == data["name"]).first():
            raise HTTPException(400, "Tier name already exists")
    for field, value in data.items():
        setattr(tier, field, value)
    db.commit()
    db.refresh(tier)
    return tier


@router.delete("/{tier_id}", status_code=204)
def delete_tier(tier_id: UUID, db: Session = Depends(get_db)):
    tier = get_tier_or_404(db, tier_id)
    db.delete(tier)
    db.commit()
