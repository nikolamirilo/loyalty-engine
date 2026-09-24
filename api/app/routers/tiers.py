from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.program import get_program
from app.models import Program, Tier
from app.schemas import RuleCondition, TierCreate, TierOut, TierUpdate
from app.services.rules.conditions import validate_conditions
from app.services.rules.fields import tier_fields
from app.services.scoping import get_scoped_or_404
from app.services.tiers import reapply_tiers

router = APIRouter(prefix="/tiers", tags=["Tiers"])


def _validate_conditions(db: Session, program: Program, conditions: list[RuleCondition]) -> list[dict]:
    return validate_conditions(db, program, tier_fields(db, program), conditions)


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
    conditions = _validate_conditions(db, program, body.conditions)
    tier = Tier(**body.model_dump(exclude={"conditions"}), conditions=conditions, program_id=program.id)
    db.add(tier)
    db.flush()
    # A new tier can immediately claim members an existing tier's rank had
    # been masking, so every member in the program is re-checked, not just
    # future changes.
    reapply_tiers(db, program.id)
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
        .order_by(Tier.rank)
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
    if "conditions" in data:
        data["conditions"] = _validate_conditions(db, program, body.conditions)
    for field, value in data.items():
        setattr(tier, field, value)
    db.flush()
    # A changed rank or condition can promote or demote members who never
    # touched anything themselves, so re-check the whole program here too.
    reapply_tiers(db, program.id)
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
    db.flush()
    # Members this tier held fall back to whatever they now qualify for
    # (`ON DELETE SET NULL` alone would just leave them tierless).
    reapply_tiers(db, program.id)
    db.commit()
