from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.program import get_program
from app.models import Program, Tier
from app.schemas import TierCreate, TierOut, TierUpdate
from app.services.scoping import get_scoped_or_404

router = APIRouter(prefix="/tiers", tags=["Tiers"])


@router.post("", response_model=TierOut, status_code=201)
def create_tier(
    body: TierCreate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    if (
        db.query(Tier)
        .filter(Tier.program_id == program.id, Tier.name == body.name)
        .first()
    ):
        raise HTTPException(400, "Tier name already exists")
    tier = Tier(**body.model_dump(), program_id=program.id)
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@router.get("", response_model=list[TierOut])
def list_tiers(
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return (
        db.query(Tier)
        .filter(Tier.program_id == program.id)
        .order_by(Tier.min_points)
        .all()
    )


@router.get("/{tier_id}", response_model=TierOut)
def get_tier(
    tier_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return get_scoped_or_404(db, Tier, tier_id, program, "Tier")


@router.patch("/{tier_id}", response_model=TierOut)
def update_tier(
    tier_id: UUID,
    body: TierUpdate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    tier = get_scoped_or_404(db, Tier, tier_id, program, "Tier")
    data = body.model_dump(exclude_none=True)
    if "name" in data and data["name"] != tier.name:
        if (
            db.query(Tier)
            .filter(Tier.program_id == program.id, Tier.name == data["name"])
            .first()
        ):
            raise HTTPException(400, "Tier name already exists")
    for field, value in data.items():
        setattr(tier, field, value)
    db.commit()
    db.refresh(tier)
    return tier


@router.delete("/{tier_id}", status_code=204)
def delete_tier(
    tier_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    tier = get_scoped_or_404(db, Tier, tier_id, program, "Tier")
    db.delete(tier)
    db.commit()
